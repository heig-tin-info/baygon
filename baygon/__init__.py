"""Baygon is a tool to run tests on executables."""

from pathlib import Path
import re

from .executable import Executable
from .schema import Schema
from .suite import TestCase, TestGroup, TestSuite


__all__ = ["TestCase", "TestGroup", "TestSuite", "Executable", "Schema"]
_PYPROJECT_VERSION_PATTERN = re.compile(
    r'^version\s*=\s*"(?P<version>[^"]+)"\s*$', re.MULTILINE
)

try:
    from importlib import metadata as importlib_metadata
except ImportError:  # pragma: no cover - Python <3.8 fallback
    import importlib_metadata  # type: ignore

try:
    from . import version as _version
except ImportError:
    _version = None

if _version is not None and getattr(_version, "version", None) is not None:
    __version__ = _version.version
else:
    try:
        __version__ = importlib_metadata.version(__name__)
    except importlib_metadata.PackageNotFoundError:
        _pyproject = Path(__file__).resolve().parent.parent / "pyproject.toml"
        if _pyproject.exists():
            match = _PYPROJECT_VERSION_PATTERN.search(
                _pyproject.read_text(encoding="utf-8")
            )
            __version__ = match.group("version") if match else None
        else:
            __version__ = None

__year__ = 2025
__copyright__ = f"Copyright {__year__} HEIG-VD"
