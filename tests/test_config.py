""" Test config file. """
from pathlib import Path
from unittest import TestCase

from baygon.suite import TestSuite

dir_path = Path(__file__).resolve(strict=True).parent


class TestConfig(TestCase):
    def test_config_file(self):
        ts = TestSuite(path='tests')
        self.assertIn('t.yml', str(ts.path))
        self.assertIn('version', ts.config)
        self.assertEqual(ts.config['version'], 1)
