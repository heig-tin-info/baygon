from __future__ import annotations

import json
from pathlib import Path

import pytest

from baygon.config.loader import (
    discover_config,
    load_config_dict,
    load_config,
    _read_config_mapping,
)
from baygon.error import ConfigError


def test_discover_config_fail_when_missing(tmp_path: Path) -> None:
    nested = tmp_path / "a" / "b"
    nested.mkdir(parents=True)
    with pytest.raises(ConfigError):
        discover_config(nested)


def test_discover_config_unknown_extension(tmp_path: Path) -> None:
    cfg = tmp_path / "config.txt"
    cfg.write_text("tests: []", encoding="utf-8")
    with pytest.raises(ConfigError):
        discover_config(cfg)


def test_load_config_dict_handles_json(tmp_path: Path) -> None:
    cfg = tmp_path / "config.json"
    cfg.write_text(json.dumps({"version": 1, "tests": []}), encoding="utf-8")
    data = load_config_dict(cfg)
    assert data["version"] == 1


def test_read_config_unknown_extension(tmp_path: Path) -> None:
    cfg = tmp_path / "cfg.bin"
    cfg.write_text("binary", encoding="utf-8")
    with pytest.raises(ConfigError):
        _read_config_mapping(cfg)


def test_load_config_uses_current_directory(tmp_path: Path, monkeypatch) -> None:
    cfg = tmp_path / "tests.yml"
    cfg.write_text("tests: []", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    assert discover_config(None) == cfg
    assert load_config(None).tests == ()
