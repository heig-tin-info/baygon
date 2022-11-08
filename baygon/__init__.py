""" Baygon is a tool to run tests on executables. """
from .executable import Executable
from .schema import Schema
from .suite import TestCase, TestGroup, TestSuite

__all__ = ['TestCase', 'TestGroup', 'TestSuite', 'Executable', 'Schema']

try:
    from . import version
    __version__ = version.version
except ImportError:
    __version__ = None

__year__ = 2022
__copyright__ = f'Copyright {__year__} HEIG-VD'
