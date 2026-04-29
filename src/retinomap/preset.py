from __future__ import annotations

from pathlib import Path

from retinomap.config import ExperimentConfig

CONFIG_DIR = Path("config")


def ensure_preset_dir(preset_dir: Path = CONFIG_DIR) -> Path:
    preset_dir.mkdir(parents=True, exist_ok=True)
    return preset_dir


def sanitize_preset_name(name: str) -> str:
    name = name.strip()

    if not name:
        raise ValueError("Preset name is empty")

    forbidden = '<>:"/\\|?*'
    for char in forbidden:
        name = name.replace(char, "_")

    return name


def preset_path(name: str, preset_dir: Path = CONFIG_DIR) -> Path:
    preset_dir = ensure_preset_dir(preset_dir)
    safe_name = sanitize_preset_name(name)

    if not safe_name.endswith(".json"):
        safe_name += ".json"

    return preset_dir / safe_name


def save_preset(
    config: ExperimentConfig,
    name: str,
    preset_dir: Path = CONFIG_DIR,
    overwrite: bool = False,
) -> Path:
    path = preset_path(name, preset_dir=preset_dir)

    if path.exists() and not overwrite:
        raise FileExistsError(f"Preset already exists: {path}")

    config.save(str(path))
    return path


def load_preset(
    name: str,
    preset_dir: Path = CONFIG_DIR,
) -> ExperimentConfig:
    path = preset_path(name, preset_dir=preset_dir)

    if not path.exists():
        raise FileNotFoundError(f"Preset not found: {path}")

    return ExperimentConfig.load(str(path))


def list_presets(preset_dir: Path = CONFIG_DIR) -> list[str]:
    preset_dir = ensure_preset_dir(preset_dir)

    return sorted(path.stem for path in preset_dir.glob("*.json"))


def delete_preset(
    name: str,
    preset_dir: Path = CONFIG_DIR,
) -> None:
    path = preset_path(name, preset_dir=preset_dir)

    if not path.exists():
        raise FileNotFoundError(f"Preset not found: {path}")

    path.unlink()
