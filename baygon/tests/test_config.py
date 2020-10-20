import os
from unittest import TestCase
from baygon.description import Tests
from baygon import Executable

dir_path = os.path.dirname(os.path.realpath(__file__))


class TestConfig(TestCase):
    def test_config_file(self, name='foobar'):
        executable = os.path.join(dir_path, 'test_full', 'main.py')
        config = os.path.join(dir_path, 'test_full', 'tests.yml')
        print(executable)
        Tests(path=config, executable=Executable(executable))
