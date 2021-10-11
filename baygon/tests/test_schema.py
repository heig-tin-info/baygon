from unittest import TestCase
from voluptuous.error import MultipleInvalid

import baygon.schema as schema


class TestSchema(TestCase):
    def test_minimal(self):
        schema.schema({
            'version': 1,
            'tests': [
                {'exit': 0}
            ]
        })

    def test_wrong_version(self):
        self.assertRaises(MultipleInvalid, schema.schema, {
            'version': 2,
            'tests': [
                {'exit': 0}
            ]
        })

    def test_filters(self):
        schema.schema({
            'version': 1,
            'filters': {
                'uppercase': True,
                'ignorespaces': True
            },
            'tests': [
            ]
        })

    def test_test_contains(self):
        schema.schema({'tests': [{'args': ['--version'], 'stderr': [{'contains': 'Version'}]}]})

    def test_empty_filters(self):
        s = schema.schema({
            'version': 1,
            'tests': []
        })
        self.assertIn('filters', s)

    # Find a way to make it exclusive...
    # def test_filters_exclusive(self):
    #     self.assertRaises(MultipleInvalid, schema.schema, {
    #         'version': 1,
    #         'filters': {
    #             'uppercase': True,
    #             'lowercase': True
    #         },
    #         'tests': [
    #         ]
    #     })
