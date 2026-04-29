from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def load_log(path: str | Path) -> pd.DataFrame:
    df = pd.read_csv(path)

    required = {
        "frame",
        "time",
        "block",
        "stim_index",
        "stimulus_type",
        "direction",
        "sweep_index",
        "phase",
    }

    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    df = df.copy()
    df["rel_time"] = df["time"] - df["time"].iloc[0]

    return df


def plot_phase_vs_time(df: pd.DataFrame, output: str | Path) -> None:
    fig, ax = plt.subplots(figsize=(10, 4))

    for (block, stim_index, direction), d in df.groupby(
        ["block", "stim_index", "direction"],
        sort=False,
    ):
        ax.plot(
            d["rel_time"],
            d["phase"],
            linewidth=0.8,
            label=f"block={block}, stim={stim_index}, {direction}",
        )

    ax.set_xlabel("Time from first frame (s)")
    ax.set_ylabel("Phase (px)")
    ax.set_title("Phase vs time")
    ax.legend(fontsize=6, ncol=2)
    fig.tight_layout()
    fig.savefig(output, dpi=200)
    plt.close(fig)


def plot_frame_interval(df: pd.DataFrame, output: str | Path) -> None:
    d = df.copy()
    d["dt"] = d["time"].diff()

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(d["frame"], d["dt"] * 1000, linewidth=0.8)

    ax.set_xlabel("Frame")
    ax.set_ylabel("Frame interval (ms)")
    ax.set_title("Frame interval")
    fig.tight_layout()
    fig.savefig(output, dpi=200)
    plt.close(fig)


def summarize_timing(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    d["dt"] = d["time"].diff()

    summary = d["dt"].describe().to_frame().T
    summary["mean_fps"] = 1.0 / d["dt"].mean()
    summary["n_frames"] = len(d)

    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("log_path", type=str)
    parser.add_argument(
        "--output-dir",
        type=str,
        default="./sanity_check",
    )
    args = parser.parse_args()

    log_path = Path(args.log_path)
    output_dir = Path(args.output_dir) / log_path.stem

    output_dir.mkdir(parents=True, exist_ok=True)

    df = load_log(log_path)

    plot_phase_vs_time(df, output_dir / "phase_vs_time.png")
    plot_frame_interval(df, output_dir / "frame_interval.png")

    summary = summarize_timing(df)
    summary.to_csv(output_dir / "summary.csv", index=False)

    print(summary)
    print(f"saved to: {output_dir}")


if __name__ == "__main__":
    main()
