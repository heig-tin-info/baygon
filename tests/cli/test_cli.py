"""Test CLI."""

import json
from pathlib import Path
from unittest import TestCase

import yaml
from typer.testing import CliRunner

from baygon.__main__ import app


class TestVersion(TestCase):
    def test_version(self):
        runner = CliRunner()
        result = runner.invoke(app, ["--version"])

        self.assertEqual(result.exit_code, 0)
        self.assertIn("version", result.output)


class TestDemo(TestCase):
    @property
    def directory(self):
        return Path(__file__).resolve(strict=True).parent

    @property
    def executable(self):
        return str(self.directory.joinpath("main.exe.py"))

    def get_config(self, name):
        return self.directory.joinpath(name)

    def test_success(self):
        runner = CliRunner()
        result = runner.invoke(
            app, [f"--config={self.get_config('success.yml')}", self.executable, "-v"]
        )

        print(f"Output: {result}")
        print(f"Executed: {self.executable}")
        print(f"Config: {self.get_config('success.yml')}")

        self.assertEqual(result.exit_code, 0)
        self.assertIn("Ran 4 tests in", result.output)
        self.assertIn("ok.", result.output)

    def test_failure(self):
        runner = CliRunner()
        result = runner.invoke(
            app, [f"--config={self.get_config('fail.yml')}", self.executable, "-v"]
        )

        print(result.output)
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Invalid exit status", result.output)
        self.assertIn("Output '3' does not equal '5' on stdout", result.output)
        self.assertIn("Output stderr does not contain tarton", result.output)
        self.assertIn("fail.", result.output)

    def test_inverse(self):
        runner = CliRunner()
        result = runner.invoke(
            app, [f"--config={self.get_config('inverse.yml')}", self.executable, "-v"]
        )

        print(result, result.output)

        self.assertEqual(result.exit_code, 0)
        self.assertIn("ok.", result.output)

    def test_ignorespaces(self):
        runner = CliRunner()
        result = runner.invoke(
            app, [f"--config={self.get_config('ignorespaces.yml')}", "-vv"]
        )

        print(result, result.output)

        self.assertEqual(result.exit_code, 0)
        self.assertIn("ok.", result.output)

    def test_triple_verbose_shows_command_panels(self):
        runner = CliRunner()
        result = runner.invoke(
            app,
            [
                "-c",
                str(self.get_config("fail.yml")),
                self.executable,
                "-vvv",
            ],
        )

        print(result.output)

        self.assertEqual(result.exit_code, 0)
        self.assertIn("Command #1", result.output)
        self.assertIn("stdin", result.output)
        self.assertIn("stdout", result.output)
        self.assertIn("stderr", result.output)

    def test_pretty_failure_renders_nested_frames(self):
        runner = CliRunner()
        result = runner.invoke(
            app,
            [
                "-c",
                str(self.get_config("fail.yml")),
                self.executable,
                "--pretty",
            ],
        )

        print(result.output)

        self.assertEqual(result.exit_code, 0)
        self.assertIn("Test 3: Version on stderr", result.output)
        self.assertIn("issues", result.output)
        self.assertIn("Command #1", result.output)
        self.assertNotIn("stdin", result.output)
        self.assertIn("stdout", result.output)
        self.assertIn("stderr", result.output)
        self.assertIn("args", result.output)

    def test_short_config_alias_c_and_table_flag(self):
        runner = CliRunner()
        result = runner.invoke(
            app,
            [
                "-c",
                str(self.get_config("success.yml")),
                "-T",
                self.executable,
                "-v",
            ],
        )

        print(result, result.output)

        self.assertEqual(result.exit_code, 0)
        self.assertIn("Test Summary", result.output)
        self.assertIn("ok.", result.output)

    def test_short_config_alias_t(self):
        runner = CliRunner()
        result = runner.invoke(
            app,
            [
                "-t",
                str(self.get_config("success.yml")),
                self.executable,
                "-v",
            ],
        )

        print(result, result.output)

        self.assertEqual(result.exit_code, 0)
        self.assertIn("ok.", result.output)

    def test_table_marks_failures(self):
        runner = CliRunner()
        result = runner.invoke(
            app,
            [
                "-c",
                str(self.get_config("fail.yml")),
                "-T",
                self.executable,
                "-v",
            ],
        )

        print(result, result.output)

        self.assertEqual(result.exit_code, 0)
        failure_rows = [
            line
            for line in result.output.splitlines()
            if "Stdout is the sum of arguments" in line
        ]
        self.assertTrue(failure_rows)
        self.assertTrue(any("FAIL" in row for row in failure_rows))

    def test_debug_mode_runs_test_suite(self):
        runner = CliRunner()
        result = runner.invoke(
            app,
            [
                "-c",
                str(self.get_config("success.yml")),
                self.executable,
                "--debug",
            ],
        )

        print(result.output)

        self.assertEqual(result.exit_code, 0)
        self.assertIn("Using configuration file", result.output)

    def test_report_json(self):
        name = "report.json"
        runner = CliRunner()
        result = runner.invoke(
            app,
            [
                f"--config={self.get_config('points.yml')}",
                f"--report={self.directory.joinpath(name)}",
                "-v",
            ],
        )

        print(result, result.output)
        print(f"Report in {self.directory.joinpath(name)}")

        self.assertTrue(self.directory.joinpath(name).exists())

        report = json.loads(self.directory.joinpath(name).read_text())

        self.assertEqual(report["total"], 4)
        self.assertEqual(report["successes"], 2)
        self.assertEqual(report["failures"], 2)
        self.assertEqual(report["skipped"], 0)
        self.assertEqual(report["points"]["total"], 10)
        self.assertEqual(report["points"]["earned"], 4)

        self.directory.joinpath(name).unlink()

    def test_report_yaml(self):
        name = "report.yaml"
        runner = CliRunner()
        result = runner.invoke(
            app,
            [
                f"--config={self.get_config('success.yml')}",
                f"--report={self.directory.joinpath(name)}",
                self.executable,
                "-v",
            ],
        )

        print(result, result.output)

        self.assertEqual(result.exit_code, 0)
        self.assertIn("ok.", result.output)
        self.assertTrue(self.directory.joinpath(name).exists())

        report = yaml.safe_load(self.directory.joinpath(name).read_text())

        self.assertEqual(report["total"], 4)
        self.assertEqual(report["successes"], 4)
        self.assertEqual(report["failures"], 0)
        self.assertEqual(report["skipped"], 0)

        self.directory.joinpath(name).unlink()
