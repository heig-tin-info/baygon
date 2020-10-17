"""
Read and validate test file.
"""
import yaml
import json

import os
from collections.abc import Sequence

from . import schema, Executable


def check_executable(executable: Executable):
    if executable and not isinstance(executable, Executable):
        raise AttributeError('Not an instance of Executable')
    return executable


def find_testfile(path=None):
    """Recursively find the tests description file."""
    if not path:
        path = os.path.dirname(os.path.realpath('.'))

    if not os.path.isdir(path):
        raise ValueError(f"Path name '{path}' is not a directory")

    for filename in ['baygon', 't', 'test', 'tests']:
        for ext in ['json', 'yml', 'yaml']:
            f = os.path.join(path, f"{filename}.{ext}")
            if os.path.exists(f):
                return f

    # Recursively search in parent directories
    if os.path.dirname(path) != path:  # Test if root directory
        return find_testfile(os.path.dirname(path))


def load(filename):
    """Load a configuration file (can be YAML or JSON)."""
    def loadYaml(filename):
        with open(filename) as fp:
            return yaml.load(fp, Loader=yaml.FullLoader)

    def loadJson(filename):
        with open(filename) as fp:
            return json.load(fp)

    extension = os.path.splitext(filename)[1]
    if extension in ['.yml', '.yaml']:
        return loadYaml(filename)
    if extension in ['.json']:
        return loadJson(filename)
    raise ValueError(f'Unknown extension: {extension}')


class Group(Sequence):
    """ Group of functional tests optionally identified by a name. """
    def __init__(self, tests, name: str = '', executable: Executable = None, id: list = []):
        self._tests = tests
        self.name = name
        self.executable = check_executable(executable)
        self._id = id

    def __len__(self):
        return len(self._tests)

    def __repr__(self):
        return self.__class__.__name__ + '(' + self.name + ', ' + repr(self._tests) + ')'

    def __getitem__(self, item):
        return self._tests[item]

    @property
    def id(self):
        return '.'.join(self._id)


class Test(dict):
    """ Functional test descriptior. """
    def __init__(self, *args, executable: Executable = None, id=[]):
        super(Test, self).__init__(*args)
        self.__dict__ = self
        self._id = id
        self.executable = check_executable(executable)

    def __repr__(self):
        return self.__class__.__name__ + '(' + super().__repr__() + ')'

    @property
    def id(self):
        return '.'.join(map(str, self._id))


class Tests(Sequence):
    _group_class = Group
    _unit_class = Test

    def __init__(self, data={}, path=None, executable: Executable = None, id=[]):
        data = schema.schema(self._load(path) if path else data)
        tests = data.pop('tests')
        self.__dict__ = data
        self.filename = path
        self.executable = check_executable(executable)
        self._id = id
        self.tests = self._build(tests)

    def _load(self, path=None):
        if not path:
            path = os.path.dirname(path.realpath('.'))

        if path and not os.path.isfile(path):
            path = find_testfile(path)
            if not path:
                raise(ValueError(
                    f"Couldn't find and configuration file in '{path}'"))

        return load(path)

    def _get_id(self, *k: int):
        return list(self._id) + list(k)

    def _build(self, tests):
        return [
            self._group_class(
                self._build(test['tests']), test['name'],
                id=self._get_id(index + 1),
                executable=self.executable)
            if 'tests' in test else
            self._unit_class(
                test,
                id=self._get_id(index + 1),
                executable=self.executable)
            for index, test in enumerate(tests)
        ]

    def __len__(self):
        return len(self.tests)

    def __repr__(self):
        return self.__class__.__name__ + '(' + repr(self.tests) + ')'

    def __getitem__(self, item):
        return self.tests[item]
