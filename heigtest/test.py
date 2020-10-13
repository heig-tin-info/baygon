"""
Build a test case for a raw test description
"""
from collections.abc import Sequence

from .executable import Executable
from .validation import TestDescription
import re

class InvalidCondition:
    def __init__(self, got, expected, message=None):
        self.got = got
        self.expected = expected
        self.message = message

class InvalidExitStatus(InvalidCondition):
    pass

class InvalidContains(InvalidCondition):
    pass

class InvalidRegex(InvalidCondition):
    pass

class InvalidEquals(InvalidCondition):
    pass

class TestCase:

    def __init__(self, executable : Executable, options : TestDescription):
        self.options = options
        self.executable = executable
        self.exe = self.executable

    def run(self):
        output = self.exe.run(*self.options.args, stdin=self.options.stdin)

        issues = []

        issues.append(self._check_exit_status(output))
        issues.append(self._check_stdout(output))
        issues.append(self._check_stderr(output))

        return issues

    def _check_exit_status(self, output):
        if not self.options.exit_status:
            return []

        expected = self.options.exit_status
        if (output.exit_status != expected):
            return [
                InvalidExitStatus(
                    output.exit_statut, expected
                )
            ]
        return []

    def _check_stdout(self, output):
        if not self.options.stdout:
            return []

        return self._check_match(output.stdout)

    def _check_stderr(self, output):
        if not self.options.stderr:
            return []

        return self._check_match(output.stderr)

    def _check_match(self, value):
        issues = []
        for case in self.options.stdout:
            if 'regex' in case:
                if not re.match(case['regex'], value):
                    issues.append(InvalidRegex(value, case['pattern']))
            if 'contains' in case:
                if case['contains'] not in value:
                    issues.append(InvalidContains(value, case['contains']))
            if 'equals' in case:
                if case['equals'] != value:
                    issues.append(InvalidEquals(value, case['equals']))

        return issues
