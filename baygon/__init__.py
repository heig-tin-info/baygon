from .executable import Executable
from .test import TestCase, TestSuite, TestGroup

__all__ = ['TestCase', 'TestGroup', 'TestSuite', 'Executable']

try:
    from . import version
    __version__ = version.version
except ImportError:
    __version__ = None

__copyright__ = 'Copyright 2020 HEIG-VD'
