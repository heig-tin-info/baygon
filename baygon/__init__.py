from .executable import Executable
from .test import TestCase, TestSuite, TestGroup
from . import version

__all__ = ['TestCase', 'TestGroup', 'TestSuite', 'Executable']

__version__ = version.version
__copyright__ = 'Copyright 2020 HEIG-VD'
