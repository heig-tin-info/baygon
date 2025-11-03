from __future__ import annotations

from pathlib import Path

import pytest

from baygon.config.loader import discover_config, load_config, load_config_dict
from baygon.error import ConfigError


def test_discover_config_finds_file_in_directory() -> None:
    config_path = discover_config("tests")
    assert config_path.name == "t.yml"


def test_discover_config_walks_up_directories(tmp_path: Path) -> None:
    project = tmp_path / "project"
    nested = project / "src" / "pkg"
    nested.mkdir(parents=True)
    config = project / "test.yaml"
    config.write_text("version: 1\ntests: []\n", encoding="utf-8")

    found = discover_config(nested)
    assert found == config.resolve()


def test_load_config_returns_suite_model() -> None:
    suite = load_config("tests")
    assert suite.version == 1
    assert len(list(suite.iter_cases())) == 4


def test_load_config_dict_augments_points() -> None:
    config = load_config_dict("tests")
    assert "compute-score" in config


def test_discover_config_unknown_extension(tmp_path: Path) -> None:
    cfg = tmp_path / "config.txt"
    cfg.write_text("version: 1\ntests: []\n", encoding="utf-8")
    with pytest.raises(ConfigError):
        discover_config(cfg)
