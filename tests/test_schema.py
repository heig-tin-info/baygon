from textwrap import dedent
from unittest import TestCase

from pydantic import ValidationError

from baygon import Schema
from baygon.error import ConfigSyntaxError


class TestSchema(TestCase):
    def test_minimal(self):
        Schema({"version": 1, "tests": [{"exit": 0}]})

    def test_wrong_version(self):
        with self.assertRaises(ValidationError):
            Schema({"version": 3, "tests": [{"exit": 0}]})

    def test_filters(self):
        Schema(
            {
                "version": 1,
                "filters": {"uppercase": True, "ignorespaces": True},
                "tests": [],
            }
        )

    def test_test_contains(self):
        Schema(
            {"tests": [{"args": ["--version"], "stderr": [{"contains": "Version"}]}]}
        )

    def test_empty_filters(self):
        s = Schema({"version": 1, "tests": []})
        self.assertIn("filters", s)

    def test_yaml_string(self):
        config = Schema(
            dedent(
                """
                version: 1
                tests:
                  - exit: 0
                """
            )
        )
        self.assertEqual(config["tests"][0]["exit"], 0)

    def test_yaml_syntax_error(self):
        with self.assertRaises(ConfigSyntaxError) as exc:
            Schema("tests:\n  - exit: [")
        self.assertIn("line", str(exc.exception))
