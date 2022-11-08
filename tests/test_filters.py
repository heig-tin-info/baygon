""" Test filters. """
from unittest import TestCase

from baygon.filters import (
    FilterIgnoreSpaces,
    FilterLowercase,
    FilterNone,
    FilterRegex,
    FilterReplace,
    Filters,
    FilterTrim,
    FilterUppercase,
)


class TestFilters(TestCase):
    def test_filter_uppercase(self):
        f = FilterUppercase()
        self.assertEqual(f('hello'), 'HELLO')

    def test_filter_lowercase(self):
        f = FilterLowercase()
        self.assertEqual(f('HELLO'), 'hello')

    def test_filter_trim(self):
        f = FilterTrim()
        self.assertEqual(f(' hello   '), 'hello')

    def test_filter_none(self):
        f = FilterNone()
        self.assertEqual(f(' hello   '), ' hello   ')

    def test_filter_replace(self):
        f = FilterReplace('hello', 'bye')
        self.assertEqual(f('hello world'), 'bye world')

    def test_filter_regex(self):
        f = FilterRegex(r'h[el]+o', 'bye')
        self.assertEqual(f('hello world'), 'bye world')

    def test_filter_ignore_spaces(self):
        f = FilterIgnoreSpaces()
        self.assertEqual(f('hello   world'), 'helloworld')

    def test_filter_multiple(self):
        f = Filters({
            'ignorespaces': True,
            'uppercase': True,
            'replace': ['L', 'Z']
        })
        self.assertEqual(f('hello   world'), 'HEZZOWORZD')
