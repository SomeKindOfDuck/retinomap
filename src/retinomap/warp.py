# src/retinomap/warp.py

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray
from scipy.ndimage import map_coordinates

from retinomap.config import ExperimentConfig

FloatArray = NDArray[np.float64]


class WarpMap:
    def __init__(self, config: ExperimentConfig):
        self.config = config

        d = config.stimulus_display
        s = config.screen

        self.height = d.height
        self.width = d.width

        # === pixel → cm ===
        cx = s.center_x_px if s.center_x_px is not None else d.width / 2
        cy = s.center_y_px if s.center_y_px is not None else d.height / 2

        x_px = np.arange(d.width)
        y_px = np.arange(d.height)

        xx_px, yy_px = np.meshgrid(x_px, y_px)

        x_cm = (xx_px - cx) / d.width * s.width_cm
        y_cm = -(yy_px - cy) / d.height * s.height_cm

        azimuth = np.degrees(
            np.arctan2(x_cm, s.distance_cm)
        )

        elevation = np.degrees(
            np.arctan2(y_cm, np.sqrt(s.distance_cm**2 + x_cm**2))
        )

        az_min, az_max = np.nanmin(azimuth), np.nanmax(azimuth)
        el_min, el_max = np.nanmin(elevation), np.nanmax(elevation)

        self.src_x = (azimuth - az_min) / (az_max - az_min) * (d.width - 1)
        self.src_y = (el_max - elevation) / (el_max - el_min) * (d.height - 1)

    def apply(self, frame: NDArray[np.uint8]) -> NDArray[np.uint8]:
        if frame.shape != (self.height, self.width):
            raise ValueError(
                f"frame shape {frame.shape} != ({self.height}, {self.width})"
            )

        warped = map_coordinates(
            frame,
            [self.src_y, self.src_x],
            order=1,
            mode="nearest",
        )

        return warped.astype(np.uint8)
