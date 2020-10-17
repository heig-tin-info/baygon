__version__ = '0.1.2'

__author__ = 'Yves Chevallier'
__description__ = 'Functional tests for teaching activities'
__email__ = 'yves.chevallier@heig-vd.ch'
__license__ = 'MIT'
__copyright__ = 'Copyright 2020 HEIG-VD'

from .executable import Executable
from .test import TestCase, TestSuite

__all__ = ['TestCase', 'TestSuite', 'Executable']
