"""Test filters."""

from unittest import TestCase
from unittest.mock import patch

from baygon.error import InvalidFilterError
from baygon.filters import (
    Filter,
    FilterEval,
    FilterFactory,
    FilterIgnoreSpaces,
    FilterLowercase,
    FilterNone,
    FilterRegex,
    FilterReplace,
    Filters,
    FilterTrim,
    FilterUppercase,
    get_registered_filters,
    register_filter,
)


class TestFilters(TestCase):
    def test_filter_uppercase(self):
        f = FilterUppercase()
        self.assertEqual(f("hello"), "HELLO")

    def test_filter_lowercase(self):
        f = FilterLowercase()
        self.assertEqual(f("HELLO"), "hello")

    def test_filter_trim(self):
        f = FilterTrim()
        self.assertEqual(f(" hello   "), "hello")

    def test_filter_none(self):
        f = FilterNone()
        self.assertEqual(f(" hello   "), " hello   ")

    def test_filter_replace(self):
        f = FilterReplace("hello", "bye")
        self.assertEqual(f("hello world"), "bye world")

    def test_filter_regex(self):
        f = FilterRegex(r"h[el]+o", "bye")
        self.assertEqual(f("hello world"), "bye world")

    def test_filter_ignore_spaces(self):
        f = FilterIgnoreSpaces()
        self.assertEqual(f("hello   world"), "helloworld")

    def test_filter_multiple(self):
        f = Filters({"ignorespaces": True, "uppercase": True, "replace": ["L", "Z"]})
        self.assertEqual(f("hello   world"), "HEZZOWORZD")

    def test_filter_base_apply_and_repr(self):
        class PassthroughFilter(Filter):
            def apply(self, value: str) -> str:
                return super().apply(value)

        f = PassthroughFilter()
        self.assertEqual(f("hello"), "hello")
        self.assertEqual(repr(f), "PassthroughFilter")

    def test_filters_sequence_behaviour(self):
        collection = Filters(FilterUppercase())
        self.assertEqual(len(collection), 1)
        self.assertIsInstance(collection[0], FilterUppercase)

        collection.extend({"lowercase": True})
        self.assertEqual(len(collection), 2)
        self.assertIn("Filters<", repr(collection))
        self.assertEqual(collection.apply("hello"), "hello")

    def test_filters_invalid_type_raises(self):
        with self.assertRaises(InvalidFilterError):
            Filters(42)

    def test_filter_eval_handles_eval_paths(self):
        evaluator = FilterEval(init=[])
        self.assertEqual(evaluator.apply("value={{1+1}}"), "value=2")
        self.assertIsNone(evaluator.exec("import math"))
        self.assertIn("FilterEval(", repr(evaluator))

    def test_filters_accept_existing_collection(self):
        base = Filters({"uppercase": True})
        clone = Filters(base)
        self.assertIsNot(clone, base)
        self.assertEqual(clone.apply("hello"), "HELLO")

    def test_filters_parse_filters_branch(self):
        base = Filters({"uppercase": True})
        from baygon import filters as module

        import builtins

        real_isinstance = builtins.isinstance

        def fake_isinstance(obj, cls):
            if obj is base and cls is module.Filter:
                return False
            return real_isinstance(obj, cls)

        with patch.dict(
            Filters._parse_filter.__globals__, {"isinstance": fake_isinstance}
        ):
            clone = module.Filters(base)

        self.assertEqual(len(clone), len(base))

    def test_filter_factory_unknown(self):
        with self.assertRaises(ValueError):
            FilterFactory("doesnotexist")

    def test_register_filter_decorator(self):
        @register_filter("custom-filter")
        class CustomFilter(Filter):
            def apply(self, value: str) -> str:
                return f"custom:{value}"

        instance = FilterFactory("custom-filter")
        self.assertIsInstance(instance, CustomFilter)
        self.assertEqual(instance("value"), "custom:value")

        class AnotherFilter(Filter):
            def apply(self, value: str) -> str:
                return value

        with self.assertRaises(ValueError):
            register_filter("custom-filter")(AnotherFilter)

    def test_get_registered_filters_returns_copy(self):
        registry = get_registered_filters()
        registry["fake"] = FilterNone
        self.assertNotIn("fake", get_registered_filters())
