"""Baygon is a tool to run tests on executables."""

from datetime import datetime

from .executable import Executable
from .schema import Schema
from .suite import TestCase, TestGroup, TestSuite

__all__ = ["TestCase", "TestGroup", "TestSuite", "Executable", "Schema"]

try:
    from . import version as _baygon_version_module  # type: ignore[attr-defined]
except ImportError:  # pragma: no cover - package metadata missing
    _baygon_version_module = None

_year_fallback = datetime.utcnow().year
__year__ = (
    _year_fallback
    if _baygon_version_module is None
    else getattr(_baygon_version_module, "__year__", _year_fallback)
)

try:
    from importlib.metadata import PackageNotFoundError
    from importlib.metadata import version as _metadata_version
except ImportError:  # pragma: no cover - Python <3.9 not supported
    __version__ = (
        getattr(_baygon_version_module, "__version__", "0.0.0")
        if _baygon_version_module is not None
        else "0.0.0"
    )
else:
    try:
        __version__ = _metadata_version("baygon")
    except PackageNotFoundError:
        __version__ = (
            getattr(_baygon_version_module, "__version__", "0.0.0")
            if _baygon_version_module is not None
            else "0.0.0"
        )

__copyright__ = f"Copyright {__year__} HEIG-VD"
