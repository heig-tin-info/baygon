""" Test config file. """
from pathlib import Path
from unittest import TestCase
from baygon.suite import TestSuite

dir_path = Path(__file__).resolve(strict=True).parent


class TestConfig(TestCase):
    def test_config_file(self):
        executable = dir_path.joinpath('test_full', 'main.py')
        config = dir_path.joinpath('test_full', 'tests.yml')
        print(f"Dir path: {dir_path}")
        print(f"Executable: {executable}")
        print(f"Config: {config}")
        TestSuite(path=config, executable=executable)
