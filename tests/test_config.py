"""Test config file."""

from pathlib import Path
from unittest import TestCase

from baygon.suite import SuiteLoader

dir_path = Path(__file__).resolve(strict=True).parent


class TestConfig(TestCase):
    def test_config_file(self):
        loader = SuiteLoader()
        context = loader.load(path="tests")

        self.assertIn("t.yml", str(context.source_path))
        self.assertIn("version", context.config)
        self.assertEqual(context.config["version"], 1)
