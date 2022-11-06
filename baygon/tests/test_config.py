""" Test config file. """
from pathlib import Path
from unittest import TestCase
from baygon.suite import TestSuite
from baygon import Executable

dir_path = Path(__file__).parent.absolute().parent


class TestConfig(TestCase):
    def test_config_file(self):
        executable = dir_path.joinpath('test_full', 'main.py')
        config = dir_path.joinpath('test_full', 'tests.yml')
        print(executable)
        TestSuite(path=config, executable=Executable(executable))
