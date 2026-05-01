from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

import numpy as np
from numpy.typing import NDArray

ImageArray = NDArray[np.uint8]
FrameState = dict[str, Any]
Direction = Literal["left", "right", "up", "down"]


@dataclass
class MovingBar:
    width: int
    height: int
    bar_width: int = 80
    speed: float = 200.0
    direction: Direction = "right"
    background: int = 0
    foreground: int = 255

    def frame(self, t: float) -> tuple[ImageArray, FrameState]:
        img = np.full((self.height, self.width), self.background, dtype=np.uint8)

        period = self._travel_distance() / self.speed
        phase = (t % period) * self.speed

        if self.direction == "right":
            x0 = int(phase - self.bar_width)
            x1 = int(phase)
            y0, y1 = 0, self.height
            self._draw_vertical_bar(img, x0, x1)

        elif self.direction == "left":
            x1 = int(self.width - phase + self.bar_width)
            x0 = int(self.width - phase)
            y0, y1 = 0, self.height
            self._draw_vertical_bar(img, x0, x1)

        elif self.direction == "down":
            y0 = int(phase - self.bar_width)
            y1 = int(phase)
            x0, x1 = 0, self.width
            self._draw_horizontal_bar(img, y0, y1)

        elif self.direction == "up":
            y1 = int(self.height - phase + self.bar_width)
            y0 = int(self.height - phase)
            x0, x1 = 0, self.width
            self._draw_horizontal_bar(img, y0, y1)

        else:
            raise ValueError(f"Unknown direction: {self.direction}")

        state = {
            "phase": phase,
            "x0": x0,
            "x1": x1,
            "y0": y0,
            "y1": y1,
        }

        return img, state

    def _travel_distance(self) -> int:
        if self.direction in ("left", "right"):
            return self.width + self.bar_width
        return self.height + self.bar_width

    def _draw_vertical_bar(self, img: ImageArray, x0: int, x1: int) -> None:
        x0 = max(0, x0)
        x1 = min(self.width, x1)

        if x1 > x0:
            img[:, x0:x1] = self.foreground

    def _draw_horizontal_bar(self, img: ImageArray, y0: int, y1: int) -> None:
        y0 = max(0, y0)
        y1 = min(self.height, y1)

        if y1 > y0:
            img[y0:y1, :] = self.foreground


@dataclass
class CheckerBar:
    width: int
    height: int
    bar_width: int = 120
    checker_size: int = 40
    reversal_rate: float = 4.0
    speed: float = 200.0
    direction: Direction = "right"
    background: int = 127

    def frame(self, t: float) -> tuple[ImageArray, FrameState]:
        img = np.full((self.height, self.width), self.background, dtype=np.uint8)

        checker = self._checkerboard(t)

        period = self._travel_distance() / self.speed
        phase = (t % period) * self.speed

        if self.direction == "right":
            x0 = int(phase - self.bar_width)
            x1 = int(phase)
            y0, y1 = 0, self.height
            self._paste_vertical_bar(img, checker, x0, x1)

        elif self.direction == "left":
            x1 = int(self.width - phase + self.bar_width)
            x0 = int(self.width - phase)
            y0, y1 = 0, self.height
            self._paste_vertical_bar(img, checker, x0, x1)

        elif self.direction == "down":
            y0 = int(phase - self.bar_width)
            y1 = int(phase)
            x0, x1 = 0, self.width
            self._paste_horizontal_bar(img, checker, y0, y1)

        elif self.direction == "up":
            y1 = int(self.height - phase + self.bar_width)
            y0 = int(self.height - phase)
            x0, x1 = 0, self.width
            self._paste_horizontal_bar(img, checker, y0, y1)

        else:
            raise ValueError(f"Unknown direction: {self.direction}")

        state = {
            "phase": phase,
            "x0": x0,
            "x1": x1,
            "y0": y0,
            "y1": y1,
        }

        return img, state


    def _checkerboard(self, t: float) -> ImageArray:
        yy, xx = np.indices((self.height, self.width))
        pattern = ((xx // self.checker_size) + (yy // self.checker_size)) % 2

        reverse = int(t * self.reversal_rate) % 2 == 1

        if reverse:
            pattern = 1 - pattern

        return (pattern * 255).astype(np.uint8)

    def _travel_distance(self) -> int:
        if self.direction in ("left", "right"):
            return self.width + self.bar_width
        return self.height + self.bar_width

    def _paste_vertical_bar(
        self,
        img: ImageArray,
        checker: ImageArray,
        x0: int,
        x1: int,
    ) -> None:
        x0 = max(0, x0)
        x1 = min(self.width, x1)

        if x1 > x0:
            img[:, x0:x1] = checker[:, x0:x1]

    def _paste_horizontal_bar(
        self,
        img: ImageArray,
        checker: ImageArray,
        y0: int,
        y1: int,
    ) -> None:
        y0 = max(0, y0)
        y1 = min(self.height, y1)

        if y1 > y0:
            img[y0:y1, :] = checker[y0:y1, :]


@dataclass
class FullFieldFlash:
    width: int
    height: int
    period: float = 1.0
    background: int = 127
    dark: int = 0
    bright: int = 255

    def frame(self, t: float) -> tuple[ImageArray, FrameState]:
        phase = (t % self.period) / self.period
        value = self.bright if phase < 0.5 else self.dark

        img = np.full((self.height, self.width), value, dtype=np.uint8)

        state = {
            "phase": phase,
            "x0": 0,
            "x1": self.width,
            "y0": 0,
            "y1": self.height,
        }

        return img, state


@dataclass
class FullFieldCheckerboard:
    width: int
    height: int
    checker_size: int = 80
    reversal_rate: float = 2.0
    background: int = 127

    def frame(self, t: float) -> tuple[ImageArray, FrameState]:
        yy, xx = np.indices((self.height, self.width))
        pattern = ((xx // self.checker_size) + (yy // self.checker_size)) % 2

        reverse = int(t * self.reversal_rate) % 2 == 1
        if reverse:
            pattern = 1 - pattern

        img = (pattern * 255).astype(np.uint8)

        state = {
            "phase": int(t * self.reversal_rate),
            "x0": 0,
            "x1": self.width,
            "y0": 0,
            "y1": self.height,
        }

        return img, state
