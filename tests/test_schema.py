from unittest import TestCase

from voluptuous.error import MultipleInvalid

from baygon import Schema


class TestSchema(TestCase):
    def test_minimal(self):
        Schema({
            'version': 1,
            'tests': [
                {'exit': 0}
            ]
        })

    def test_wrong_version(self):
        self.assertRaises(MultipleInvalid, Schema, {
            'version': 3,
            'tests': [
                {'exit': 0}
            ]
        })

    def test_filters(self):
        Schema({
            'version': 1,
            'filters': {
                'uppercase': True,
                'ignorespaces': True
            },
            'tests': [
            ]
        })

    def test_test_contains(self):
        Schema({'tests': [{'args': ['--version'], 'stderr': [{'contains': 'Version'}]}]})

    def test_empty_filters(self):
        s = Schema({
            'version': 1,
            'tests': []
        })
        self.assertIn('filters', s)
