# src/retinomap/config.py

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Literal

StimulusType = Literal["moving_bar", "checker_bar", "sparse_noise"]
Direction = Literal["left", "right", "up", "down"]


@dataclass
class ScreenConfig:
    width_cm: float = 40.0
    height_cm: float = 30.0
    distance_cm: float = 20.0
    enable_warp: bool = True

    center_x_px: float | None = None
    center_y_px: float | None = None

    def resolve_center(self, width_px: int, height_px: int):
        cx = self.center_x_px if self.center_x_px is not None else width_px / 2
        cy = self.center_y_px if self.center_y_px is not None else height_px / 2
        return cx, cy


@dataclass
class StimulusDisplayConfig:
    screen_index: int = 1
    width: int = 800
    height: int = 600
    fps: float = 60.0
    fullscreen: bool = True


@dataclass
class ControlDisplayConfig:
    screen_index: int = 0
    width: int = 800
    height: int = 600


@dataclass
class StimulusConfig:
    stimulus_type: StimulusType = "checker_bar"

    direction: Direction = "right"
    speed: float = 100.0

    bar_width: int = 80
    checker_size: int = 40
    checker_reversal_rate: float = 4.0
    background: int = 127

    grid_size: int = 40
    density: float = 0.05
    seed: int = 0


@dataclass
class TrialConfig:
    iti: float = 0.0
    repetitions: int = 5
    sweeps_per_direction: int = 1
    directions: tuple[Direction, ...] = ("up", "right", "down", "left")
    inter_stimulus_interval: float = 2.0
    randomize: bool = False
    seed: int = 0


@dataclass
class PhotodiodeConfig:
    enable: bool = True
    size_px: int = 50
    margin_px: int = 0
    value: int = 255


@dataclass
class LogConfig:
    enable: bool = True
    directory: str = "log"



@dataclass
class ExperimentConfig:
    experiment_id: str = ""
    screen: ScreenConfig = field(default_factory=ScreenConfig)
    stimulus_display: StimulusDisplayConfig = field(default_factory=StimulusDisplayConfig)
    control_display: ControlDisplayConfig = field(default_factory=ControlDisplayConfig)
    stimulus: StimulusConfig = field(default_factory=StimulusConfig)
    photodiode: PhotodiodeConfig = field(default_factory=PhotodiodeConfig)
    trial: TrialConfig = field(default_factory=TrialConfig)
    log: LogConfig = field(default_factory=LogConfig)

    def to_dict(self) -> dict:
        return asdict(self)

    def save(self, path: str) -> None:
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, path: str) -> "ExperimentConfig":
        with open(path, "r") as f:
            data = json.load(f)

        return cls(
            experiment_id=data.get("experiment_id", ""),
            stimulus_display=StimulusDisplayConfig(**data.get("display", {})),
            control_display=ControlDisplayConfig(**data.get("display", {})),
            stimulus=StimulusConfig(**data.get("stimulus", {})),
            trial=TrialConfig(**data.get("trial", {})),
            log=LogConfig(**data.get("log", {})),
        )
