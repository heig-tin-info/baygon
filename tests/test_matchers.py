from unittest import TestCase

import baygon.matchers
from baygon.matchers import (
    InvalidCondition,
    InvalidRegex,
    MatchBase,
    MatcherFactory,
    get_registered_matchers,
    register_matcher,
)


class TestMatchers(TestCase):
    def test_equals(self):
        self.assertIsNone(baygon.matchers.MatchEquals(42)(42))
        self.assertIsInstance(
            baygon.matchers.MatchEquals(42)(43), baygon.matchers.InvalidEquals
        )

    def test_contains(self):
        self.assertIsNone(baygon.matchers.MatchContains("foo")("i am foobar"))
        self.assertIsInstance(
            baygon.matchers.MatchContains("baz")("i am foobar"),
            baygon.matchers.InvalidContains,
        )

    def test_regex(self):
        self.assertIsNone(baygon.matchers.MatchRegex(r"fo{2,}")("i am foobar"))
        self.assertIsInstance(
            baygon.matchers.MatchRegex(r"fa{2,}")("i am foobar"),
            baygon.matchers.InvalidRegex,
        )

    def test_matcher_factory_unknown(self):
        with self.assertRaises(ValueError):
            MatcherFactory("missing")

    def test_register_matcher(self):
        @register_matcher("alwayspass")
        class MatchAlways(baygon.matchers.MatchBase):
            def __call__(self, value, **kwargs):
                return None

        instance = MatcherFactory("alwayspass")
        self.assertIsInstance(instance, MatchAlways)
        self.assertIsNone(instance("value"))

        class MatchOther(baygon.matchers.MatchBase):
            def __call__(self, value, **kwargs):
                return None

        with self.assertRaises(ValueError):
            register_matcher("alwayspass")(MatchOther)

    def test_invalid_condition_messages_and_registry(self):
        issue = InvalidCondition("value", "expected", on="stdout")
        self.assertIn("expected", str(issue))
        self.assertIn("InvalidCondition", repr(issue))

        regex_issue = InvalidRegex("output", "pattern", on="stdout")
        self.assertIn("pattern", str(regex_issue))

        registry = get_registered_matchers()
        registry["new"] = MatchBase  # mutate copy
        self.assertNotIn("new", get_registered_matchers())

    def test_match_base_not_implemented(self):
        class DummyMatch(MatchBase):
            def __call__(self, value, **kwargs):
                return super().__call__(value, **kwargs)

        with self.assertRaises(NotImplementedError):
            DummyMatch()("value")
