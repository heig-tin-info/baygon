"""Test CLI."""

from pathlib import Path
from unittest import TestCase
import json
import yaml
from click.testing import CliRunner

from baygon.__main__ import cli


class TestVersion(TestCase):
    def test_version(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["--version"])

        self.assertEqual(result.exit_code, 0)
        self.assertIn("version", result.output)


class TestDemo(TestCase):
    @property
    def directory(self):
        return Path(__file__).resolve(strict=True).parent

    @property
    def executable(self):
        return str(self.directory.joinpath("main.py"))

    def get_config(self, name):
        return self.directory.joinpath(name)

    def test_success(self):
        runner = CliRunner()
        result = runner.invoke(
            cli, [f"--config={self.get_config('success.yml')}", self.executable, "-v"]
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
            cli, [f"--config={self.get_config('fail.yml')}", self.executable, "-v"]
        )

        print(result.output)
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Invalid exit status", result.output)
        self.assertIn("Output 3 not equals 5 on stdout", result.output)
        self.assertIn("Output stderr does not contain tarton", result.output)
        self.assertIn("fail.", result.output)

    def test_inverse(self):
        runner = CliRunner()
        result = runner.invoke(
            cli, [f"--config={self.get_config('inverse.yml')}", self.executable, "-v"]
        )

        print(result, result.output)

        self.assertEqual(result.exit_code, 0)
        self.assertIn("ok.", result.output)

    def test_ignorespaces(self):
        runner = CliRunner()
        result = runner.invoke(
            cli, [f"--config={self.get_config('ignorespaces.yml')}", "-vv"]
        )

        print(result, result.output)

        self.assertEqual(result.exit_code, 0)
        self.assertIn("ok.", result.output)

    def test_report_json(self):
        name = "report.json"
        runner = CliRunner()
        result = runner.invoke(
            cli,
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

        report = json.loads(self.directory.joinpath(name).read_text())

        self.assertEqual(report["total"], 4)
        self.assertEqual(report["successes"], 4)
        self.assertEqual(report["failures"], 0)
        self.assertEqual(report["skipped"], 0)

        self.directory.joinpath(name).unlink()

    def test_report_yaml(self):
        name = "report.yaml"
        runner = CliRunner()
        result = runner.invoke(
            cli,
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
