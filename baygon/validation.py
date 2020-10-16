"""
Read and validate test file.
"""
import yaml
import json

from os import path
from collections.abc import Sequence

from . import schema 

def find_testfile():
    for filename in ['baygon', 't', 'test', 'tests']:
        for ext in ['json', 'yml', 'yaml']:
            f = f"{filename}.{ext}"
            if path.exists(f):
                return f

def load(filename):
    def loadYaml(filename):
        with open(filename) as fp:
            return yaml.load(fp, Loader=yaml.FullLoader)

    def loadJson(filename):
        with open(filename) as fp:
            return json.load(fp)

    def validate(data):
        return schema.schema(data)

    extension = path.splitext(filename)[1]
    if extension in ['.yml', '.yaml']:
        return validate(loadYaml(filename))
    if extension in ['.json']:
        return validate(loadJson(filename))
    raise ValueError(f'Unknown extension: {extension}')



class Group(Sequence):
    def __init__(self, tests, name=''):
        self.tests = tests
        self.name = name

    def __len__(self):
        return len(self.tests)

    def __repr__(self):
        return '<' + self.__class__.__name__ + ':' + self.name + ':' + repr(self.tests) + '>'

    def __getitem__(self, item):
        return self.tests[item]


class Test(dict):
    def __init__(self, *args, **kwargs):
        super(Test, self).__init__(*args, **kwargs)
        self.__dict__ = self

    @property
    def exit_status(self):
        return self['exit-status'] if 'exit-status' in self else None

    def __repr__(self):
        return '<' + self.__class__.__name__ + ':'  + super().__repr__() + '>'


class Tests(Sequence):
    def __init__(self, filename):
        self.filename = filename
        self.data = load(filename)
        self.name = self.data['name']
        self.filters = self.data['filters'] if 'filters' in self.data else {}
        self.executable = self.data['executable'] if 'executable' in self.data else None
        self.tests = self._build(self.data['tests'])

    def _build(self, tests):
        return [
            Group(self._build(test['tests']), test['name']) if 'tests' in test else Test(test)
            for test in tests
        ]

    def __len__(self):
        return len(self.tests)

    def __repr__(self):
        return '<' + self.__class__.__name__ + ':' + repr(self.tests) + '>'

    def __getitem__(self, item):
        return self.tests[item]
