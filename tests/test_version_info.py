from __future__ import annotations

import importlib
import sys
from types import ModuleType

import pytest


@pytest.fixture
def restore_baygon_module():
    import baygon

    original_version = getattr(baygon, "__version__", None)
    yield baygon

    # Restore canonical module state after manipulations
    if "baygon.version" in sys.modules:
        del sys.modules["baygon.version"]
    importlib.reload(baygon)
    if original_version is not None:
        baygon.__version__ = original_version


def test_version_loaded_from_internal_module(restore_baygon_module):
    baygon = restore_baygon_module

    dummy_version = ModuleType("baygon.version")
    dummy_version.version = "9.9.9"
    sys.modules["baygon.version"] = dummy_version

    importlib.reload(baygon)

    assert baygon.__version__ == "9.9.9"


def test_version_falls_back_to_pyproject(monkeypatch, restore_baygon_module):
    baygon = restore_baygon_module

    sys.modules.pop("baygon.version", None)

    import importlib.metadata as real_metadata

    def fake_version(_name: str) -> str:
        raise real_metadata.PackageNotFoundError

    monkeypatch.setattr(real_metadata, "version", fake_version)

    importlib.reload(baygon)

    assert isinstance(baygon.__version__, str) or baygon.__version__ is None


def test_version_defaults_to_none_when_no_metadata(monkeypatch, restore_baygon_module):
    baygon = restore_baygon_module

    sys.modules.pop("baygon.version", None)

    import importlib.metadata as real_metadata

    def fake_version(_name: str) -> str:
        raise real_metadata.PackageNotFoundError

    monkeypatch.setattr(real_metadata, "version", fake_version)
    monkeypatch.setattr("baygon.Path.exists", lambda self: False)

    importlib.reload(baygon)

    assert baygon.__version__ is None
