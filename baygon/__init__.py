"""Baygon is a tool to run tests on executables."""

from .executable import Executable
from .schema import Schema
from .suite import TestCase, TestGroup, TestSuite

__all__ = ["TestCase", "TestGroup", "TestSuite", "Executable", "Schema"]

try:
    from importlib.metadata import PackageNotFoundError
    from importlib.metadata import version as _metadata_version
except ImportError:  # pragma: no cover - Python <3.9 not supported
    _metadata_version = None  # type: ignore[assignment]
else:
    try:
        __version__ = _metadata_version("baygon")
    except PackageNotFoundError:
        _metadata_version = None  # type: ignore[assignment]

if "_metadata_version" in globals() and _metadata_version is not None:
    pass
else:
    try:
        from .version import __version__  # type: ignore[attr-defined]
    except ImportError:
        __version__ = "0.0.0"

__year__ = 2022
__copyright__ = f"Copyright {__year__} HEIG-VD"
