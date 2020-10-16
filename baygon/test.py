"""
Build a test case for a raw test description
"""
from collections.abc import Sequence

from .executable import Executable
from .validation import Group, Test, Tests

from . import schema, error
import logging

logger = logging.getLogger()


def match(options, value, where=None):
    issues = []

    for case in options:
        if 'uppercase' in case:
            value = value.upper()

        if 'lowercase' in case:
            value = value.lower()

        if 'trim' in case:
            logger.debug('Trimming str')
            value = value.strip()

        if 'regex' in case:
            logger.debug('Checking regex')
            if not value.grep(case['regex']):
                issues += [error.InvalidRegex(value, case['regex'], on=where)]

        if 'contains' in case:
            logger.debug('Checking contains')
            logger.debug(' - value :' + value)
            if case['contains'] not in value:
                logger.debug('New issue : ' + case['contains'])
                issues += [error.InvalidContains(value,
                                           case['contains'], on=where)]
        if 'equals' in case:
            logger.debug('Checking equals')
            if case['equals'] != value:
                issues += [error.InvalidEquals(value, case['equals'], on=where)]

    return issues


class TestCase:
    def __init__(self, options: Test, executable: Executable = None, id=[]):
        self.options = schema.test(options)
        self.name = options.name
        self.executable = executable
        self.exe = self.executable
        self._id = id

    def run(self):

        output = self.exe.run(*self.options.args, stdin=self.options.stdin)
        issues = []
        issues += self._check_exit_status(output)
        issues += self._check_stdout(output)
        issues += self._check_stderr(output)
        return issues

    def _check_exit_status(self, output):
        if self.options.exit_status is None:
            return []
        expected = self.options.exit_status
        if (output.exit_status != expected):
            return [
                error.InvalidExitStatus(
                    output.exit_status, expected
                )
            ]
        return []

    def _check_stdout(self, output):
        if self.options.stdout is None:
            return []
        return match(self.options, output.stdout, where='stdout')

    def _check_stderr(self, output):
        if self.options.stderr is None:
            return []
        return match(self.options, output.stderr, where='stderr')


    @property
    def id(self):
        return '.'.join(map(str, self._id))

    def __repr__(self):
        return f'<TestCase {self.id}:{self.options.name}>'


class TestGroup(Sequence):
    def __init__(self, tests):
        self._tests = tests

    def __len__(self):
        return len(self._tests)

    def __getitem__(self, item):
        return self._tests[item]

    def __repr__(self):
        return repr(self._tests)


class TestSuite(TestGroup):
    def __init__(self, tests: Tests, executable: Executable = None, id=[]):
        self._id = id
        self.name = tests.name
        self._executable = executable if executable is not None else None
        self._tests = list(self._build(tests))

    def _build(self, tests):
        for index, test in enumerate(tests):
            yield [TestCase, TestSuite][isinstance(test, Group)](
                test, self._executable, id=self._id + [index + 1])

    @property
    def id(self):
        return '.'.join(map(str, self._id))

    def run(self):
        return [u.run() for u in self._tests]
