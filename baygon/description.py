"""
Read and validate test file.
"""
import yaml
import json

import os
from collections.abc import Sequence

from . import schema 

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
    if os.path.dirname(path) != path: # Test if root directory
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
    def __init__(self, tests, name:str='', id:list=[]):
        self._tests = tests
        self.name = name
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
    def __init__(self, *args, **kwargs):
        super(Test, self).__init__(*args, **kwargs)
        self.__dict__ = self

    def __repr__(self):
        return self.__class__.__name__ + '('  + super().__repr__() + ')'


class Tests(Sequence):
    def __init__(self, data={}, path=None):
        data = schema.schema(self._load(path) if path else data)
        tests = data.pop('tests')
        self.__dict__ = data
        self.filename = path
        self.tests = self._build(tests)

    def _load(self, path=None):
        if not data and not path:
            path = os.path.dirname(path.realpath('.'))            

        if path and not os.path.isfile(path):
            path = find_testfile(path)
            if not path:
                raise(ValueError(f"Couldn't find and configuration file in '{path}'"))

        return load(path)

    def _build(self, tests):
        return [
            Group(self._build(test['tests']), test['name']) if 'tests' in test else Test(test)
            for test in tests
        ]

    def __len__(self):
        return len(self.tests)

    def __repr__(self):
        return self.__class__.__name__ + '(' + repr(self.tests) + ')'

    def __getitem__(self, item):
        return self.tests[item]
