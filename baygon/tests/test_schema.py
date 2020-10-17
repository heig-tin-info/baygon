from unittest import TestCase
from voluptuous.error import MultipleInvalid

import baygon.schema as schema

class TestSchema(TestCase):
    def test_minimal(self):
        schema.schema({
            'version': 1,
            'tests': [
                {'exit-status': 0}
            ]
        })

    def test_filters(self):
        schema.schema({
            'version': 1,
            'filters': {
                'uppercase': True
            },
            'tests': [
            ]
        })

    def test_empty_filters(self):
        s = schema.schema({
            'version': 1,
            'tests': []
        })
        self.assertIn('filters', s)

    def test_filters_exclusive(self):
        self.assertRaises(MultipleInvalid, schema.schema, {
            'version': 1,
            'filters': {
                'uppercase': True,
                'lowercase': True
            },
            'tests': [
            ]
        })
