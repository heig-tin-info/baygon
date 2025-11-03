from unittest import TestCase

from baygon.suite import SuiteService


class TestEval(TestCase):
    def setUp(self):
        self.service = SuiteService()

    def test_eval(self):
        report = self.service.run(
            data={
                "filters": {"trim": True},
                "eval": True,
                "tests": [
                    {
                        "args": ["{{ i = 10 }}"],
                        "stdout": {"equals": "{{ i }}"},
                        "exit": 0,
                    }
                ],
            },
            executable="/bin/echo",
        )
        self.assertEqual(report.failures, 0)

    def test_add(self):
        report = self.service.run(
            data={
                "filters": {"trim": True},
                "eval": True,
                "tests": [
                    {
                        "stdin": "({{ i = 10 }} + {{ j = 10 }}) * 42",
                        "args": ["-e", "print eval <STDIN>"],
                        "stdout": {"equals": "{{ (i + j) * 42}}"},
                        "exit": 0,
                    }
                ],
            },
            executable="/bin/perl",
        )
        self.assertEqual(report.failures, 0)

    def test_random(self):
        stdin = "({{ i = randint(10,1000) }} + {{ j = randint(1,10) }}) * 42"
        report = self.service.run(
            data={
                "filters": {"trim": True},
                "eval": True,
                "tests": [
                    {
                        "stdin": stdin,
                        "args": ["-e", "print eval <STDIN>"],
                        "stdout": {"equals": "{{ (i + j) * 42}}"},
                        "exit": 0,
                    }
                ],
            },
            executable="/bin/perl",
        )
        self.assertEqual(report.failures, 0)

    def test_repeat(self):
        report = self.service.run(
            data={
                "filters": {"trim": True},
                "eval": True,
                "tests": [
                    {
                        "repeat": 10,
                        "stdin": "({{ i = iter(0) }} + {{ j = iter(10) }}) * 42",
                        "args": ["-e", "print eval <STDIN>"],
                        "stdout": {"equals": "{{ (i + j) * 42 }}"},
                        "exit": 0,
                    }
                ],
            },
            executable="/bin/perl",
        )
        self.assertEqual(report.failures, 0)
