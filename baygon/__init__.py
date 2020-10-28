__version__ = '0.1.8'

__author__ = 'Yves Chevallier'
__description__ = 'Functional tests for teaching activities'
__email__ = 'yves.chevallier@heig-vd.ch'
__license__ = 'MIT'
__copyright__ = 'Copyright 2020 HEIG-VD'

from .executable import Executable
from .test import TestCase, TestSuite, TestGroup

__all__ = ['TestCase', 'TestGroup', 'TestSuite', 'Executable']
