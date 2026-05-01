from __future__ import annotations

import random
from typing import Iterator

from retinomap.config import Direction, ExperimentConfig
from retinomap.stimuli import CheckerBar, MovingBar

# =========================
# stimulus
# =========================

def build_stimulus(config: ExperimentConfig, direction: Direction):
    s = config.stimulus
    d = config.stimulus_display

    if s.stimulus_type == "moving_bar":
        return MovingBar(
            width=d.width,
            height=d.height,
            bar_width=s.bar_width,
            speed=s.speed,
            direction=direction,
        )

    elif s.stimulus_type == "checker_bar":
        return CheckerBar(
            width=d.width,
            height=d.height,
            bar_width=s.bar_width,
            checker_size=s.checker_size,
            speed=s.speed,
            direction=direction,
            background=s.background,
            reversal_rate=s.checker_reversal_rate,
        )

    else:
        raise ValueError(f"Unknown stimulus_type: {s.stimulus_type}")

def compute_sweep_duration(config: ExperimentConfig, direction: Direction) -> float:
    d = config.stimulus_display
    s = config.stimulus

    if direction in ("left", "right"):
        travel_distance = d.width + s.bar_width
    else:
        travel_distance = d.height + s.bar_width

    return travel_distance / s.speed

# =========================
# trials
# =========================

def build_direction_sequence(config: ExperimentConfig) -> list[Direction]:
    t = config.trial

    directions = list(t.directions) * t.repetitions

    if t.randomize:
        rng = random.Random(t.seed)
        rng.shuffle(directions)

    return directions

def build_blocks(config: ExperimentConfig) -> Iterator[dict]:
    t = config.trial

    directions = list(t.directions)

    for block_index in range(t.repetitions):
        if t.randomize:
            rng = random.Random(t.seed + block_index)
            block_directions = directions.copy()
            rng.shuffle(block_directions)
        else:
            block_directions = directions

        yield {
            "block_index": block_index,
            "directions": block_directions,
            "sweeps_per_direction": t.sweeps_per_direction,
            "inter_stimulus_interval": t.inter_stimulus_interval,
            "iti": t.iti,
        }
