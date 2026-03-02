from __future__ import annotations

from pathlib import Path

import pytest

from baygon.suite import SuiteLoader, SuiteService, find_testfile, load_config


def test_find_testfile_returns_none(tmp_path: Path) -> None:
    assert find_testfile(tmp_path) is None


def test_suite_loader_rejects_both_sources() -> None:
    loader = SuiteLoader()
    with pytest.raises(
        ValueError, match=r"Provide either 'data' or 'path', not both\."
    ):
        loader.load(data={}, path="somepath")


def test_suite_service_load_delegates(tmp_path: Path) -> None:
    loader = SuiteLoader()
    context = loader.load(data={"tests": []}, cwd=tmp_path)
    assert context.name == ""

    service = SuiteService(loader)
    loaded = service.load(data={"tests": []}, cwd=tmp_path)
    assert loaded.base_dir == tmp_path.resolve()


def test_load_config_function_reads_existing_config() -> None:
    config_path = Path("tests") / "t.yml"
    config = load_config(config_path)
    assert "tests" in config
