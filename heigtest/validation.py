"""
Read and validate test file.
"""
import os.path
import yaml
import json
from os import path
from voluptuous import Schema, IsFile, Coerce, Required, Any, All, Number, Optional
from collections.abc import Sequence

from .executable import Executable


def AsList(x):
    return All(x, lambda u: [u])


Match = Any(
    All(Number(), Coerce(str), lambda x: [{'equals': x}]),
    All(str, lambda x: [{'equals': x}]),
    [
        {
            Optional('equals'): str,
            Optional('regex'): str,
            Optional('contains'): str
        }
    ]
)

Matches = Any(
    [Match],
    All(Match, lambda x: [x])
)

schema = Schema({
    Required('version'): 1,
    Required('executable'): IsFile('Missing configuration file'),
    Required('tests'): [
        {
            Optional('name'): str,
            Optional('args'): [Any(str, All(Number(), Coerce(str)))],
            Optional('stdin', default=None): Any(None, str, [str]),
            Optional('stdout', default=[]): Match,
            Optional('stderr', default=[]): Match,
            Optional('exit-status'): All(Any(int, bool), Coerce(int))
        }
    ]
})


class TestDescription(dict):
    @property
    def name(self):
        return self['name']

    @property
    def args(self):
        return self['args']

    @property
    def exit_status(self):
        return self['exit-status'] if 'exit-status' in self else None

    @property
    def stdin(self):
        return self['stdin']

    @property
    def stdout(self):
        return self['stdout']

    @property
    def stderr(self):
        return self['stderr']

    @property
    def id(self):
        return self.id

    def __repr__(self):
        return '<TestDescription:' + super().__repr__() + '>'


class TestDescriptionList(Sequence):
    basenames = ['t', 'test', 'tests']

    def __init__(self, filename=None):
        if not filename:
            filename = self.find_testfile()

        self.filename = filename

        self._raw = self.load(filename)
        data = self.validate(self._raw)

        self._executable = Executable(data['executable'])
        self._tests = [
            TestDescription(test) for test in data['tests']
        ]

    def find_testfile(self):
        for filename in self.basenames:
            for ext in ['json', 'yml', 'yaml']:
                f = f"{filename}.{ext}"
                if path.exists(f):
                    return f

    def load(self, filename):
        extension = os.path.splitext(filename)[1]
        if extension in ['.yml', '.yaml']:
            return self.loadYaml(filename)
        if extension in ['.json']:
            return self.loadJson(filename)
        raise ValueError(f'Unknown extension: {extension}')

    def loadYaml(self, filename):
        with open(filename) as fp:
            return yaml.load(fp, Loader=yaml.FullLoader)

    def loadJson(self, filename):
        with open(filename) as fp:
            return json.load(fp)

    def validate(self, data):
        return schema(data)

    def __len__(self):
        return len(self._tests)

    def __repr__(self):
        return '<tests:' + repr(self._tests) + '>'

    def __getitem__(self, item):
        return self._tests[item]

    @property
    def executable(self):
        return self._executable
