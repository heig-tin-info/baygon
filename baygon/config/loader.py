"""Load Baygon configuration files and return immutable suite models."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from baygon.core.models import SuiteModel, build_suite_model
from baygon.error import ConfigError
from baygon.schema import Schema
from baygon.score import compute_points


_CANDIDATE_BASENAMES: tuple[str, ...] = ("baygon", "t", "test", "tests")
_SUPPORTED_EXTENSIONS: tuple[str, ...] = (".json", ".yml", ".yaml")


def discover_config(path: str | Path | None) -> Path:
    """Locate a configuration file starting from the given path or CWD."""
    start = _resolve_start(path)

    if start.is_file():
        if start.suffix.lower() not in _SUPPORTED_EXTENSIONS:
            raise ConfigError(f"Unknown file extension '{start.suffix}' for '{start}'.")
        return start

    current = start
    while True:
        found = _scan_directory(current)
        if found is not None:
            return found
        if current.parent == current:
            break
        current = current.parent

    raise ConfigError("Couldn't find configuration file.")


def load_config(path: str | Path | None) -> SuiteModel:
    """Load a configuration file and build a SuiteModel."""
    config_path = discover_config(path)
    config_dict = load_config_dict(config_path)
    return build_suite_model(config_dict)


def load_config_dict(path: str | Path | None) -> dict[str, Any]:
    """Load a configuration file and return the validated dictionary form."""
    config_path = discover_config(path)
    data = _read_config_mapping(config_path)
    compute_points(data)
    return data


def _resolve_start(path: str | Path | None) -> Path:
    if path is None:
        return Path.cwd().resolve()
    candidate = Path(path)
    try:
        return candidate.resolve(strict=True)
    except FileNotFoundError as exc:  # pragma: no cover - guard rails
        raise ConfigError(
            f"Couldn't find configuration file in '{candidate}'."
        ) from exc


def _scan_directory(directory: Path) -> Path | None:
    for name in _CANDIDATE_BASENAMES:
        for extension in _SUPPORTED_EXTENSIONS:
            candidate = directory / f"{name}{extension}"
            if candidate.exists():
                return candidate.resolve()
    return None


def _read_config_mapping(path: Path) -> dict[str, Any]:
    suffix = path.suffix.lower()
    if suffix in {".yml", ".yaml"}:
        text = path.read_text(encoding="utf-8")
        return Schema(text)
    if suffix == ".json":
        with path.open(encoding="utf-8") as fp:
            return Schema(json.load(fp))
    raise ConfigError(f"Unknown file extension '{path.suffix}' for '{path}'.")
