""" Test suite. """
import json
from pathlib import Path
import yaml
from .schema import Schema
from .filters import Filters
from .id import Id
from .executable import Executable
from . import error


def find_testfile(path=None):
    """Recursively find the tests description file."""
    if not path:
        path = Path('.').absolute()
    elif isinstance(path, str):
        path = Path(path)

    if not path.is_dir():
        raise ValueError(f"Path name '{path}' is not a directory")

    for filename in ['baygon', 't', 'test', 'tests']:
        for ext in ['json', 'yml', 'yaml']:
            f = path.joinpath(f"{filename}.{ext}")
            if f.exists():
                return f

    # Recursively search in parent directories
    if path.parent == path:  # Test if root directory
        return None

    return find_testfile(path.parent)


def load_config(path=None):
    """Load a configuration file (can be YAML or JSON)."""
    path = path or find_testfile(path)

    if not path.exists():
        raise ValueError(
            f"Couldn't find and configuration file in '{path.absolute()}'")

    if path.suffix in ['.yml', '.yaml']:
        with open(path, 'rt', encoding="utf-8") as fp:
            data = yaml.safe_load(fp)
    elif path.suffix in ['.json']:
        with open(path, 'rt', encoding="utf-8") as fp:
            data = json.load(fp)
    else:
        raise ValueError(f"Unknown file extension: {path.suffix}")

    return Schema(data)


def match(options: list, value: str, where=None, inverse=False) -> list:
    """ Match a value against a list of options. """
    issues = []
    for case in options:
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


class TestFilterMixin:
    """ Mixin for tests that can have filters. """

    def __init__(self, config, *args, **kwargs):
        self.filters = Filters()

        if 'filters' in config:
            self.filters.extend(config['filters'])


class TestBaseMixin(TestFilterMixin):
    """ Base class for tests. """

    def __init__(self, config, executable=None):
        super().__init__(config, executable)
        self.name = config['name']
        self.id = Id(config['test_id'])
        self.points = config['points']

        if executable is not None and self.config['executable'] is not None:
            raise ValueError(
                "Executable can't be overridden in the test configuration")

        self.executable = Executable(executable) if executable else None

    def __repr__(self):
        return f"{self.__class__.__name__}<{self.id}. {self.name}>"


class TestGroupMixin:
    """ Mixin for tests that can have sub-tests. """

    def __init__(self, config, executable=None, *args, **kwargs):
        super().__init__(config, executable, *args, **kwargs)
        self.tests = []
        for test in config['tests']:
            if 'tests' in test:
                self.tests.append(TestGroup(test, executable))
            else:
                self.tests.append(Test(test, executable))

    def __len__(self):
        return len(self.tests)

    def __getitem__(self, item):
        return self.tests[item]

    def run(self):
        """ Run the tests. """
        for test in self.tests:
            test.run()

    def get_points(self):
        """ Return the total number of points. """
        return sum(test.points for test in self.tests)


class Test(TestBaseMixin):
    """ A single test. """

    def __init__(self, config, *args, **kwargs):
        super().__init__(config, *args, **kwargs)

        self.args = config.get('args', [])
        self.env = config.get('env', {})

        self.stdin = config.get('stdin', '')
        self.stdout = config.get('stdout', [])
        self.stderr = config.get('stderr', [])

        self.exit = config.get('exit', None)

    def run(self):
        """ Run the tests. """
        if not isinstance(self.executable, Executable):
            raise ValueError('Not a valid executable')

        output = self.executable.run(*self.args, stdin=self.stdin)

        return [
            *self._check_exit_status(output.exit_status),
            *self._check_stdout(self.filters.filter(output.stdout)),
            *self._check_stderr(self.filters.filter(output.stdout))
        ]

    def _check_exit_status(self, output):
        if (output != self.exit):
            return [error.InvalidExitStatus(output, self.exit)]
        return []

    def _check_stdout(self, output):
        return match(self.stdout, output, where='stdout')

    def _check_stderr(self, output):
        if self.stderr is None:
            return []
        return match(self.stderr, output, where='stderr')


class TestGroup(TestGroupMixin, TestBaseMixin):
    """ A group of tests. """

    def __init__(self, config, executable, *args, **kwargs):
        super().__init__(config, executable, *args, **kwargs)
        if executable is not None and self.config['executable'] is not None:
            raise ValueError(
                "Executable can't be overridden in the test configuration")

        self.executable = Executable(executable) if executable else None


class TestSuite(TestGroupMixin, TestFilterMixin):
    """ Test suite. """

    def __init__(self, path=None, executable=None):
        self.path = find_testfile(path)
        self.config = load_config(self.path)
        self.version = self.config.get('version')
        if executable is not None and self.config['executable'] is not None:
            raise ValueError(
                "Executable can't be specified in both the config and the command line")

        self.executable = Executable(executable) if executable else None

        super().__init__(config=self.config, executable=self.executable)
