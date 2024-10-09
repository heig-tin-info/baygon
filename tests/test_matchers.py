from unittest import TestCase

import baygon.matchers


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
