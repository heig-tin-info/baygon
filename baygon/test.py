"""
Inherit Description classes and provide a `run` method
that eventually returns a list of errors.
"""
from . import error, description, Executable


def filter_value(value, options: dict = {}):
    if 'uppercase' in options:
        value = value.upper()
    if 'lowercase' in options:
        value = value.lower()
    if 'trim' in options:
        value = value.strip()
    if 'ignorespaces' in options:
        value = value.replace(' ', '')
    return value


def match(options, value, where=None, inverse=False):
    issues = []
    for case in options:
        value = filter_value(value, case)
        if 'regex' in case:
            if (not value.grep(case['regex'])) ^ inverse:
                issues += [error.InvalidRegex(value, case['regex'], on=where)]
        if 'contains' in case:
            if (not value.contains(case['contains'])) ^ inverse:
                issues += [
                    error.InvalidContains(
                        value, case['contains'], on=where)]
        if 'equals' in case:
            if (case['equals'] != value) ^ inverse:
                issues += [
                    error.InvalidEquals(value, case['equals'], on=where)]
        if 'not' in case:
            issues += match(case['not'], value, where, inverse=True)

    return issues


class TestCase(description.Test):
    def run(self):
        if self._skip:
            return None

        if not isinstance(self.executable, Executable):
            raise ValueError('Not a valid executable')

        output = self.executable.run(*self.args, stdin=self.stdin)

        return [
            *self._check_exit_status(output),
            *self._check_stdout(output),
            *self._check_stderr(output)
        ]

    def _check_exit_status(self, output):
        if 'exit' not in self:
            return []
        if (output.exit_status != self.exit):
            return [
                error.InvalidExitStatus(
                    output.exit_status, self.exit
                )
            ]
        return []

    def _check_stdout(self, output):
        if self.stdout is None:
            return []
        return match(self.stdout, output.stdout, where='stdout')

    def _check_stderr(self, output):
        if self.stderr is None:
            return []
        return match(self.stderr, output.stderr, where='stderr')


class TestGroup(description.Group):
    def run(self):
        return [u.run() for u in self]


class TestSuite(description.Tests):
    _unit_class = TestCase
    _group_class = TestGroup

    def run(self):
        return [u.run() for u in self]
