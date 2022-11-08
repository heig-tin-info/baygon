""" Test suite. """
import json
from pathlib import Path
from .error import InvalidExecutableError, ConfigError
import yaml

from . import error
from .executable import Executable
from .filters import Filters
from .id import Id
from .schema import Schema
from .str import GreppableString


def find_testfile(path=None):
    """Recursively find the tests description file."""
    if not path:
        path = Path('.')
    elif isinstance(path, str):
        path = Path(path)

    path = path.resolve(strict=True)

    if path.is_file():
        return path

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
    path = find_testfile(path)

    if not path.exists():
        raise ConfigError(
            f"Couldn't find and configuration file in '{path.resolve()}'")

    with open(path, 'rt', encoding="utf-8") as fp:
        if path.suffix in ['.yml', '.yaml']:
            return Schema(yaml.safe_load(fp))
        if path.suffix in ['.json']:
            return Schema(json.load(fp))

    raise ConfigError(f"Unknown file extension '{path.suffix}' for '{path}'")


class BaseMixin:
    """ Base mixin to prevent super() failure.
    Ensure it will be the last MRO (Method Resolution Order)."""

    def __init__(self, *args, **kwargs):
        pass


class FilterMixin(BaseMixin):
    """ Mixin for tests that can have filters. """

    def __init__(self, *args, **kwargs):
        config = args[0]

        if 'parent' in kwargs and hasattr(kwargs['parent'], 'filters'):
            self.filters = kwargs['parent'].filters
        else:
            self.filters = Filters()

        if 'filters' in config:
            self.filters.extend(config['filters'])

        super().__init__(*args, **kwargs)


class ExecutableMixin(BaseMixin):
    """ Mixin for tests that have an executable. """

    def __init__(self, *args, **kwargs):
        config = args[0]
        self.cwd = kwargs['parent'].cwd

        if hasattr(kwargs['parent'], 'executable'):
            executable = kwargs['parent'].executable
        else:
            executable = None

        if executable is not None and config['executable'] is not None:
            raise InvalidExecutableError(
                "Executable can't be overridden")

        if config['executable'] is not None:
            exe = self.cwd.joinpath(config['executable']).resolve(strict=True)
            self.executable = Executable(exe)
        else:
            self.executable = Executable(executable)

        super().__init__(*args, **kwargs)


class NamedMixin(BaseMixin):
    """ Mixin for tests having a name. """

    def __init__(self, *args, **kwargs):
        config = args[0]

        self.name = config['name']
        self.id = Id(config['test_id'])
        self.points = config['points']

        super().__init__(*args, **kwargs)

    def __repr__(self):
        return f"{self.__class__.__name__}<{self.id}. {self.name}>"


class GroupMixin(BaseMixin):
    """ Mixin for tests that can have sub-tests. """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        config = args[0]
        self.tests = []
        for test in config['tests']:
            if 'tests' in test:
                self.tests.append(TestGroup(test, parent=self))
            else:
                self.tests.append(TestCase(test, parent=self))

    def __len__(self):
        return len(self.tests)

    def __getitem__(self, item):
        return self.tests[item]

    def run(self, flatten=False):
        """ Run the tests. """
        if flatten:
            issues = []
            for test in self.tests:
                run = test.run()
                issues += (run if isinstance(run, list) else [run])
        else:
            issues = [test.run() for test in self.tests]
        return issues

    def get_points(self):
        """ Return the total number of points. """
        return sum(test.points for test in self.tests)


class TestCase(NamedMixin, ExecutableMixin, FilterMixin):
    """ A single test. """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        config = args[0]

        self.args = config.get('args', [])
        self.env = config.get('env', {})

        self.stdin = config.get('stdin', '')
        self.stdout = config.get('stdout', [])
        self.stderr = config.get('stderr', [])

        self.exit = config.get('exit', None)
        self.config = config
        self.output = None
        self.issues = []

    def run(self):
        """ Run the tests. """
        if not isinstance(self.executable, Executable):
            raise InvalidExecutableError(
                f"Test {self.id}, not a valid executable: {self.executable}")

        self.output = output = self.executable.run(*self.args,
                                                   stdin=self.stdin)

        self.issues = [
            *self._check_exit_status(output.exit_status),
            *self._check_stdout(output.stdout),
            *self._check_stderr(output.stderr)
        ]
        return self.issues

    def _check_exit_status(self, output):
        if self.exit is None:  # No exit status specified
            return []
        if output != self.exit:
            return [error.InvalidExitStatus(output, self.exit,
                                            name=self.name, id=self.id)]
        return []

    def _check_stdout(self, output):
        return self._match(self.stdout, output, where='stdout')

    def _check_stderr(self, output):
        if self.stderr is None:
            return []
        return self._match(self.stderr, output, where='stderr')

    def _match(self, options: list, value: str,
               where=None, inverse=False) -> list:
        """ Match a value against a list of options. """
        issues = []
        for case in options:
            value = GreppableString(self.filters.extend(case.get('filters', {}))(value))

            if 'regex' in case:
                if (not value.grep(case['regex'])) ^ inverse:
                    issues += [error.InvalidRegex(value, case['regex'],
                                                  on=where, name=self.name,
                                                  id=self.id)]
            if 'contains' in case:
                if (not value.contains(case['contains'])) ^ inverse:
                    issues += [
                        error.InvalidContains(
                            value, case['contains'], on=where,
                            name=self.name, id=self.id)]
            if 'equals' in case:
                if (case['equals'] != value) ^ inverse:
                    issues += [
                        error.InvalidEquals(value, case['equals'], on=where,
                                            name=self.name, id=self.id)]
            if 'not' in case:
                issues += self._match(case['not'], value, where, inverse=True)

        return issues


class TestGroup(NamedMixin, ExecutableMixin, FilterMixin, GroupMixin):
    """ A group of tests. """


class TestSuite(ExecutableMixin, FilterMixin, GroupMixin):
    """ Test suite. """
    __test__ = False  # Don't run this class as a test

    def __init__(self, data: dict = None, path=None, executable=None, cwd=None):
        if isinstance(data, dict):
            self.config = Schema(data)
            cwd = Path.cwd()
        else:
            self.path = find_testfile(path)
            cwd = self.path
            self.config = load_config(self.path)

        self.name = self.config.get('name', 'Test Suite')
        self.version = self.config.get('version')

        class Root:
            def __init__(self, executable):
                self.executable = Executable(executable)
                self.cwd = cwd.resolve(strict=True).parent

        super().__init__(self.config, parent=Root(executable))
