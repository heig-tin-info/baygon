"""Baygon is a tool to run tests on executables."""

from .executable import Executable
from .schema import Schema
from .suite import TestCase, TestGroup, TestSuite

__all__ = ["TestCase", "TestGroup", "TestSuite", "Executable", "Schema"]

try:
    from . import version as _version
except ImportError:
    try:
        from importlib.metadata import PackageNotFoundError
        from importlib.metadata import version as _metadata_version
    except ImportError:  # pragma: no cover - Python <3.9 not supported
        __version__ = None
    else:
        try:
            __version__ = _metadata_version("baygon")
        except PackageNotFoundError:
            __version__ = None
else:
    __version__ = _version.version

__year__ = 2022
__copyright__ = f"Copyright {__year__} HEIG-VD"
