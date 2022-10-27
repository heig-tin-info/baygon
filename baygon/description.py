"""
Read and validate test file.
"""
import os
import json
from collections.abc import Sequence, Mapping
import yaml

from . import schema, Executable


def check_executable(executable: Executable, filters=None):
    """ Check if the given executable is valid. """
    if executable and not isinstance(executable, Executable):
        raise AttributeError('Not an instance of Executable class')

    executable.filters.update(filters or {})

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

    return None


class TestFile(Mapping):
    """ TestFile properties """

    def __init__(self, filename: str):
        self._data = schema.schema(self._load(filename))

    def _load(self, filename):
        """Load a configuration file (can be YAML or JSON)."""
        def load_yaml(filename):
            with open(filename, 'rt', encoding="utf-8") as fp:
                return yaml.safe_load(fp)

        def load_json(filename):
            with open(filename, 'rt', encoding="utf-8") as fp:
                return json.load(fp)

        extension = os.path.splitext(filename)[1]
        if extension in ['.yml', '.yaml']:
            return load_yaml(filename)
        if extension in ['.json']:
            return load_json(filename)
        raise ValueError(f'Unknown extension: {extension}')

    def __getitem__(self, key):
        return self._data[key]

    def __iter__(self):
        for key in self._data:
            yield key

    def __len__(self):
        return len(self._data)


class WithId:
    def __init__(self):
        super().__init__()
        self._id = None

    @property
    def id(self):
        """ Return the id of the object. """
        return '.'.join(map(str, self._id))


class TestSequence(Sequence):
    """ A sequence of tests. """

    def __init__(self):
        super().__init__()
        self._tests = []

    def __len__(self):
        return len(self._tests)

    def __repr__(self):
        return self.__class__.__name__ + '(' + repr(self._tests) + ')'

    def __getitem__(self, item):
        return self._tests[item]


class Test(Mapping, WithId):
    """ Functional test descriptor. """

    def __init__(self, *args, executable: Executable = None, id=None, skip=False):
        super().__init__()
        self.__dict__ = self
        self._id = id or []
        self._skip = skip
        self.executable = check_executable(executable)

    def __repr__(self):
        return self.__class__.__name__ + '(' + super().__repr__() + ')'


class Group(TestSequence, WithId):
    """ Group of functional tests optionally identified by a name. """

    def __init__(self, tests, name: str = '', executable: Executable = None,
                 id: list = [], skip=False):
        self._tests = tests
        self.name = name
        self.executable = check_executable(executable)
        self._skip = skip
        self._id = id


class Tests(TestSequence, WithId):
    """ A sequence of tests. """
    _group_class = Group
    _unit_class = Test

    def __init__(self, data: dict = None, path: str = None,
                 executable: Executable = None,
                 id=None, skip: bool = False):
        super().__init__()

        if not isinstance(data, dict):
            data = self._load(path)

        data = schema.schema(data)  # Validate

        tests = data.pop('tests')
        self.__dict__ = data
        self.filename = path
        self.executable = check_executable(executable, self.filters)
        self._id = id or []
        self._skip = skip
        self._tests = list(self._build(tests, self._id, self.executable))

    def _load(self, path=None):
        if not path:
            path = os.path.realpath('.')

        if path and not os.path.isfile(path):
            old_path = path
            path = find_testfile(path)
            if not path:
                raise ValueError(
                    f"Couldn't find and configuration file in '{old_path}'")

        return load(path)

    def _build(self, tests, id=[], executable=None, skip=False):
        for index, test in enumerate(tests, start=1):
            new_id = id + [index]
            kwargs = {'id': new_id, 'skip': skip, 'executable': executable}
            if 'executable' in test and test['executable'] is not None:
                if os.path.isfile(test['executable']):
                    kwargs['executable'] = Executable(test['executable'])
                else:
                    kwargs['skip'] = True

            if 'tests' in test:
                yield self._group_class(
                    list(self._build(test['tests'], **kwargs)),
                    name=test['name'], **kwargs)
            else:
                yield self._unit_class(test, **kwargs)
