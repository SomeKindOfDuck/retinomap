from __future__ import annotations

import os
from datetime import datetime
from typing import TextIO

from retinomap.config import ExperimentConfig


class FrameLogger:
    def __init__(self, base_dir: str = "log") -> None:
        self.base_dir = base_dir
        self.file: TextIO | None = None
        self.frame_idx = 0
        self.timestamp: str | None = None
        self.log_path: str | None = None
        self.config_path: str | None = None

    def start(self, config: ExperimentConfig | None = None) -> str:
        os.makedirs(self.base_dir, exist_ok=True)

        self.timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")

        if config is not None:
            prefix = []
            print("Yeah")
            if config.experiment_id:
                prefix.append(config.experiment_id)

            log_file = "-".join(prefix + [self.timestamp]) + ".csv"
            config_file = "-".join(prefix + [self.timestamp]) + "_config.json"
            self.log_path = os.path.join(self.base_dir, log_file)
            self.config_path = os.path.join(self.base_dir, config_file)

        else:
            self.log_path = os.path.join(self.base_dir, f"{self.timestamp}.csv")
            self.config_path = os.path.join(self.base_dir, f"{self.timestamp}_config.json")

        self.file = open(self.log_path, "w")
        self.file.write(
            "frame,time,block,stim_index,stimulus_type,direction,"
            "sweep_index,phase,x0,x1,y0,y1\n"
        )

        if config is not None:
            config.save(self.config_path)

        return self.log_path

    def log(self, *, time, block, stim_index, stimulus_type,
            direction, sweep_index, phase, x0, x1, y0, y1):

        self.frame_idx += 1

        self.file.write(
            f"{self.frame_idx},{time},{block},{stim_index},{stimulus_type},"
            f"{direction},{sweep_index},{phase},{x0},{x1},{y0},{y1}\n"
        )

    def close(self) -> None:
        if self.file is not None:
            self.file.close()
            self.file = None
