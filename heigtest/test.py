"""
Build a test case for a raw test description
"""
from collections.abc import Sequence

from .executable import Executable
from .validation import TestDescription, TestDescriptionList
import re
import logging

logger = logging.getLogger()


class InvalidCondition:
    def __init__(self, got, expected, message=None, on=None):
        self.got = got
        self.expected = expected
        self.message = message
        self.on = on

    def __str__(self):
        return f'Expected "{self.expected}", but got "{self.got}"'


class InvalidExitStatus(InvalidCondition):
    def __str__(self):
        return f'Invalid exit status. Expected {self.expected}, but got {self.got}'


class InvalidContains(InvalidCondition):
    pass


class InvalidRegex(InvalidCondition):
    def __str__(self):
        return f'Invalid value on {self.on}. Expected to match regex /{self.expected}/'


class InvalidEquals(InvalidCondition):
    def __str__(self):
        return f'Invalid value on {self.on}. Expected exactly "{self.expected}", but got "{self.got}"'


class TestCase:

    def __init__(self, executable: Executable, options: TestDescription, id=None):
        self.options = options
        self.name = options.name
        self.executable = executable
        self.exe = self.executable
        self.id = id

    def run(self):
        output = self.exe.run(*self.options.args, stdin=self.options.stdin)
        logger.debug('Running test : %s' % self.options.name)
        issues = []
        issues += self._check_exit_status(output)
        issues += self._check_stdout(output)
        issues += self._check_stderr(output)
        return issues

    def _check_exit_status(self, output):
        if self.options.exit_status is None:
            return []

        logger.debug('Checking exit status %d =? %d' %
                     (self.options.exit_status, output.exit_status))
        expected = self.options.exit_status
        if (output.exit_status != expected):
            return [
                InvalidExitStatus(
                    output.exit_status, expected
                )
            ]
        return []

    def _check_stdout(self, output):
        if self.options.stdout is None:
            return []

        return self._check_match(output, 'stdout')

    def _check_stderr(self, output):
        if self.options.stderr is None:
            return []

        return self._check_match(output, 'stderr')

    def _check_match(self, output, where):
        issues = []
        value = getattr(output, where)

        for case in getattr(self.options, where):
            if 'regex' in case:
                logger.debug('Checking regex')
                if not value.grep(case['regex']):
                    issues += [InvalidRegex(value, case['regex'], on=where)]
            if 'contains' in case:
                logger.debug('Checking contains')
                if case['contains'] not in value:
                    issues += [InvalidContains(value,
                                               case['contains'], on=where)]
            if 'equals' in case:
                logger.debug('Checking equals')
                if case['equals'] != value:
                    issues += [InvalidEquals(value, case['equals'], on=where)]

        return issues

    def __repr__(self):
        return f'<TestCase:{self.options.name}>'


class TestSuite(Sequence):
    def __init__(self, tests: TestDescriptionList):
        self._tests = [
            TestCase(tests.executable, option, id + 1)
            for id, option in enumerate(tests)
        ]

    def __len__(self):
        return len(self._tests)

    def __getitem__(self, item):
        return self._tests[item]

    def __repr__(self):
        return repr(self._tests)

    def run(self):
        return [
            u.run() for u in self._tests
        ]
