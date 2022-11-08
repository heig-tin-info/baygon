
from pathlib import Path
from unittest import TestCase

import baygon
from baygon import error

dir_path = Path(__file__).resolve(strict=True).parent


class TestDemo(TestCase):
    def setUp(self):
        self.exe = baygon.Executable(dir_path.joinpath('main.py'))

    def test_minimal(self):
        print(dir_path)
        ts = baygon.TestSuite(path=dir_path, executable=self.exe)
        self.assertEqual(ts.run(), [[[], []], [], []])

    def test_error_exit_status(self):
        ts = baygon.TestSuite(
            {'tests': [{'exit': 12}]},
            executable=self.exe
        )

        self.assertIsInstance(ts.run()[0][0], error.InvalidExitStatus)

    def test_error_stdout(self):
        ts = baygon.TestSuite(
            {'tests': [{'args': [30, 40], 'stdout': 42}]},
            executable=self.exe
        )
        self.assertIsInstance(ts.run()[0][0], error.InvalidEquals)

    def test_error_stderr(self):
        ts = baygon.TestSuite(
            {'tests': [{'args': ['--version'], 'stderr': 42}]},
            executable=self.exe
        )
        self.assertIsInstance(ts.run()[0][0], error.InvalidEquals)

    def test_contains_stderr(self):
        ts = baygon.TestSuite(
            {'tests': [{'args': ['--version'], 'stderr': [{'contains': 'Version'}]}]},
            executable=self.exe
        )
        self.assertEqual(ts.run(), [[]])

    def test_uppercase_filter_with_contains_stderr(self):
        ts = baygon.TestSuite(
            {
                'filters': {
                    'uppercase': True
                },
                'tests': [
                    {
                        'args': ['--version'],
                        'stderr': [{'contains': 'VERSION'}]
                    }
                ]
            },
            executable=self.exe
        )
        t = ts.run()

        self.assertEqual(t, [[]])

    def test_lowercase_filter_with_contains_stderr(self):
        ts = baygon.TestSuite(
            {
                'filters': {
                    'lowercase': True
                },
                'tests': [
                    {
                        'args': ['--version'],
                        'stderr': [{'contains': 'version'}]
                    }
                ]
            },
            executable=self.exe
        )
        t = ts.run()
        self.assertEqual(t, [[]])
