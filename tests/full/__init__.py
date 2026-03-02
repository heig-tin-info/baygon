from pathlib import Path
from unittest import TestCase

import baygon
from baygon import error
from baygon.suite import SuiteExecutor, SuiteLoader, SuiteService

dir_path = Path(__file__).resolve(strict=True).parent


class TestDemo(TestCase):
    def setUp(self):
        self.exe = baygon.Executable(dir_path.joinpath("main.exe.py"))
        self.loader = SuiteLoader()
        self.executor = SuiteExecutor()
        self.service = SuiteService()

    def _run_from_data(self, data):
        return self.service.run(
            data=data,
            cwd=dir_path,
            executable=self.exe.filename,
        )

    def test_minimal(self):
        context = self.loader.load(path=dir_path)
        report = self.executor.run(
            context,
            executable=self.exe.filename,
        )

        self.assertEqual(report.failures, 0)
        self.assertEqual(report.successes, report.total)

    def test_error_exit_status(self):
        report = self._run_from_data({"tests": [{"exit": 12}]})

        self.assertEqual(report.failures, 1)
        self.assertIsInstance(report.cases[0].issues[0], error.InvalidExitStatus)

    def test_error_stdout(self):
        report = self._run_from_data({"tests": [{"args": [30, 40], "stdout": 42}]})
        self.assertEqual(report.failures, 1)
        self.assertIsInstance(report.cases[0].issues[0], error.InvalidEquals)

    def test_error_stderr(self):
        report = self._run_from_data({"tests": [{"args": ["--version"], "stderr": 42}]})
        self.assertEqual(report.failures, 1)
        self.assertIsInstance(report.cases[0].issues[0], error.InvalidEquals)

    def test_contains_stderr(self):
        report = self._run_from_data(
            {"tests": [{"args": ["--version"], "stderr": [{"contains": "Version"}]}]}
        )
        self.assertEqual(report.failures, 0)

    def test_uppercase_filter_with_contains_stderr(self):
        report = self._run_from_data(
            {
                "filters": {"uppercase": True},
                "tests": [{"args": ["--version"], "stderr": [{"contains": "VERSION"}]}],
            }
        )

        self.assertEqual(report.failures, 0)

    def test_lowercase_filter_with_contains_stderr(self):
        report = self._run_from_data(
            {
                "filters": {"lowercase": True},
                "tests": [{"args": ["--version"], "stderr": [{"contains": "version"}]}],
            }
        )
        self.assertEqual(report.failures, 0)
