from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable

import numpy as np
import pygame
from PySide6.QtWidgets import QApplication

import retinomap.config as cfg
from retinomap.factory import (build_blocks, build_stimulus,
                               compute_sweep_duration)
from retinomap.logger import FrameLogger
from retinomap.warp import WarpMap


def draw_photodiode_square(frame: np.ndarray, config: cfg.ExperimentConfig) -> np.ndarray:
    p = config.photodiode

    if not p.enable:
        return frame

    frame = frame.copy()

    y0 = p.margin_px
    y1 = p.margin_px + p.size_px
    x1 = frame.shape[1] - p.margin_px
    x0 = x1 - p.size_px

    frame[y0:y1, x0:x1] = p.value

    return frame


@dataclass
class StimulusPlayer:
    config: cfg.ExperimentConfig
    stop_requested: bool = False
    preview_callback: Callable[[np.ndarray], None] | None = None
    preview_fps: float = 10.0
    _last_preview_time: float = 0.0
    _current_window_state: tuple | None = None

    def open_window(self) -> None:
        if not pygame.get_init():
            pygame.init()
        self.reopen_window()

    def reopen_window(self) -> None:
        import os

        d = self.config.stimulus_display

        if pygame.display.get_init():
            pygame.display.quit()

        os.environ["SDL_VIDEO_WINDOW_POS"] = f"{d.window_x},{d.window_y}"

        # pygame.display.init()

        # desktop_sizes = pygame.display.get_desktop_sizes()

        # if d.screen_index < 0 or d.screen_index >= len(desktop_sizes):
        #     raise ValueError(
        #         f"Invalid screen_index={d.screen_index}. "
        #         f"Available displays: 0..{len(desktop_sizes) - 1}, "
        #         f"sizes={desktop_sizes}"
        #     )

        # if d.fullscreen:
        #     size = desktop_sizes[d.screen_index]
        # else:
        #     size = (d.width, d.height)

        # flags = pygame.NOFRAME

        # self.screen = pygame.display.set_mode(
        #     size,
        #     flags,
        #     display=d.screen_index,
        # )

        # actual_width, actual_height = self.screen.get_size()
        # d.width = actual_width
        # d.height = actual_height
        pygame.display.init()

        desktop_sizes = pygame.display.get_desktop_sizes()

        if d.screen_index < 0 or d.screen_index >= len(desktop_sizes):
            raise ValueError(
                f"Invalid screen_index={d.screen_index}. "
                f"Available displays: 0..{len(desktop_sizes) - 1}, "
                f"sizes={desktop_sizes}"
            )

        if d.fullscreen:
            size = desktop_sizes[d.screen_index]
        else:
            size = (d.width, d.height)

        flags = pygame.NOFRAME

        self.screen = pygame.display.set_mode(
            size,
            flags,
            display=d.screen_index,
        )

        actual_width, actual_height = self.screen.get_size()
        d.width = actual_width
        d.height = actual_height

        self.warp_map = None
        if self.config.screen.enable_warp:
            self.warp_map = WarpMap(self.config)

        pygame.display.set_caption("retinomap")
        self.clock = pygame.time.Clock()
        self.draw_gray()

    def _get_window_state(self) -> tuple:
        d = self.config.stimulus_display

        if d.fullscreen:
            return (
                d.fullscreen,
                d.screen_index,
                d.window_x,
                d.window_y,
            )

        return (
            d.fullscreen,
            d.screen_index,
            d.width,
            d.height,
            d.window_x,
            d.window_y,
        )

    def ensure_window(self) -> None:
        new_state = self._get_window_state()

        if self._current_window_state == new_state:
            return

        self.reopen_window()

        self._current_window_state = self._get_window_state()

    def draw_gray(self) -> None:
        self.screen.fill((127, 127, 127))
        pygame.display.flip()
        pygame.event.pump()

    def close_window(self) -> None:
        pygame.quit()

    def request_stop(self) -> None:
        self.stop_requested = True

    def reset_stop(self) -> None:
        self.stop_requested = False

    def play_experiment(self) -> None:
        d = self.config.stimulus_display
        l = self.config.log

        if not hasattr(self, "screen"):
            self.open_window()

        screen = self.screen
        clock = self.clock

        logger: FrameLogger | None = None
        if l.enable:
            logger = FrameLogger(base_dir=l.directory)
            log_path = logger.start(config=self.config)
            print(f"log saved to: {log_path}")
            print(f"config saved to: {logger.config_path}")

        running = True
        try:
            for block in build_blocks(self.config):
                if not running:
                    break

                block_index = block["block_index"]

                for stim_index, direction in enumerate(block["directions"]):
                    if not running:
                        break

                    stim = build_stimulus(self.config, direction)

                    sweep_duration = compute_sweep_duration(self.config, direction)
                    sweeps = block["sweeps_per_direction"]
                    duration = sweep_duration * sweeps

                    running = self.play_stimulus(
                        screen=screen,
                        clock=clock,
                        stimulus=stim,
                        duration=duration,
                        fps=d.fps,
                        logger=logger,
                        block_index=block_index,
                        stim_index=stim_index,
                        stimulus_type=self.config.stimulus.stimulus_type,
                        direction=direction,
                        sweep_duration=sweep_duration,
                    )

                    if not running:
                        break

                    if block["inter_stimulus_interval"] > 0:
                        running = self.run_iti(
                            screen=screen,
                            clock=clock,
                            duration=block["inter_stimulus_interval"],
                            fps=d.fps,
                        )

                if not running:
                    break

                if block["iti"] > 0:
                    running = self.run_iti(
                        screen=screen,
                        clock=clock,
                        duration=block["iti"],
                        fps=d.fps,
                    )
        finally:
            if logger is not None:
                logger.close()
            # pygame.quit()
            self.draw_gray()

    def play_stimulus(
        self,
        screen: pygame.Surface,
        clock: pygame.time.Clock,
        stimulus,
        duration: float,
        fps: float,
        logger: FrameLogger | None = None,
        block_index: int = 0,
        stim_index: int = 0,
        stimulus_type: str = "",
        direction: str = "",
        sweep_duration: float = 1.0,
    ) -> bool:
        start_time = time.perf_counter()

        while True:
            QApplication.processEvents()

            now = time.perf_counter()
            t = now - start_time

            if self.stop_requested:
                self.draw_gray()
                return False

            if t >= duration:
                return True

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    return False

            frame, state = stimulus.frame(t)
            if self.warp_map is not None:
                frame = self.warp_map.apply(frame)

            frame = draw_photodiode_square(frame, self.config)

            self._emit_preview(frame)

            if frame.ndim != 2:
                raise ValueError(f"Expected 2D grayscale frame, got shape={frame.shape}")

            if frame.dtype != np.uint8:
                frame = frame.astype(np.uint8)

            if logger is not None:
                sweep_index = int(t // sweep_duration)

                logger.log(
                    time=now,
                    block=block_index,
                    stim_index=stim_index,
                    stimulus_type=self.config.stimulus.stimulus_type,
                    direction=direction,
                    sweep_index=sweep_index,
                    phase=state["phase"],
                    x0=state["x0"],
                    x1=state["x1"],
                    y0=state["y0"],
                    y1=state["y1"],
                )

            rgb = np.repeat(frame[:, :, None], 3, axis=2)
            surface = pygame.surfarray.make_surface(np.transpose(rgb, (1, 0, 2)))

            screen.blit(surface, (0, 0))
            pygame.display.flip()

            clock.tick(fps)

    def run_iti(
        self,
        screen: pygame.Surface,
        clock: pygame.time.Clock,
        duration: float,
        fps: float,
    ) -> bool:
        start_time = time.perf_counter()

        while True:
            QApplication.processEvents()

            t = time.perf_counter() - start_time

            if t >= duration:
                return True

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    return False

            screen.fill((127, 127, 127))

            p = self.config.photodiode
            if p.enable:
                y0 = p.margin_px
                y1 = p.margin_px + p.size_px
                x1 = self.config.stimulus_display.width - p.margin_px
                x0 = x1 - p.size_px

                pygame.draw.rect(
                    screen,
                    (0, 0, 0),
                    pygame.Rect(x0, y0, p.size_px, p.size_px),
                )

            pygame.display.flip()

            preview_frame = np.full(
                (
                    self.config.stimulus_display.height,
                    self.config.stimulus_display.width,
                ),
                127,
                dtype=np.uint8,
            )

            p = self.config.photodiode
            if p.enable:
                y0 = p.margin_px
                y1 = p.margin_px + p.size_px
                x1 = self.config.stimulus_display.width - p.margin_px
                x0 = x1 - p.size_px

                preview_frame[y0:y1, x0:x1] = 0

            self._emit_preview(preview_frame)

            clock.tick(fps)

    def set_preview_callback(
        self,
        callback: Callable[[np.ndarray], None] | None,
        fps: float = 10.0,
    ) -> None:
        self.preview_callback = callback
        self.preview_fps = fps
        self._last_preview_time = 0.0

    def _emit_preview(self, frame: np.ndarray) -> None:
        if self.preview_callback is None:
            return

        now = time.perf_counter()
        if now - self._last_preview_time < 1.0 / self.preview_fps:
            return

        self._last_preview_time = now
        self.preview_callback(frame)
