import os.path
import yaml
import json
from os import path
from voluptuous import Schema, Coerce, Any, All, Number
from collections.abc import Iterable

Match = Any(
    str,
    {
        'pattern': str,
    }
)

Matches = Any(
    Match,
    [Match],
)

schema = Schema({
    'version': 1,
    'executable': str,
    'tests': [
        {
            'name': str,
            'args': [All(Any(str, Number), Coerce(int))],
            'stdin': Any(str, [str]),
            'stdout': Match,
            'stderr': Match,
            'exit-status': bool
        }
    ]
})

class TestList(Iterable):
    basenames = ['t', 'test', 'tests']

    def __init__(self, filename=None):
        if not filename:
            filename = self.find_testfile

        data = self.validate(self.load(filename))
        self._tests = data.tests
        self._name = data.name

    def find_testfile(self):
        for filename in self.basenames:
            for ext in ['json', 'yml', 'yaml']:
                f = f"{filename}.{ext}"
                if path.exists(f):
                    return f

    def load(self, filename):
        extension = os.path.splitext(filename)[1]
        if extension in ['yml', 'yaml']:
            return self.loadYaml(filename)
        if extension in ['json']:
            return self.loadJson(filename)

    def loadYaml(self, filename):
        with open(filename) as fp:
            return yaml.load(fp, Loader=yaml.FullLoader)

    def loadJson(self, filename):
        with open(filename) as fp:
            return json.load(fp)

    def validate(self, data):
        return schema(data)

    def __iter__(self):
        for test in self._tests:
            yield test
