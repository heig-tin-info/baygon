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


def test_filter_uppercase():
    f = FilterUppercase()
    assert f("hello") == "HELLO"


def test_filter_lowercase():
    f = FilterLowercase()
    assert f("HELLO") == "hello"


def test_filter_trim():
    f = FilterTrim()
    assert f(" hello   ") == "hello"


def test_filter_none():
    f = FilterNone()
    assert f(" hello   ") == " hello   "


def test_filter_replace():
    f = FilterReplace("hello", "bye")
    assert f("hello world") == "bye world"


def test_filter_regex():
    f = FilterRegex(r"h[el]+o", "bye")
    assert f("hello world") == "bye world"


def test_filter_ignore_spaces():
    f = FilterIgnoreSpaces()
    assert f("hello   world") == "helloworld"


def test_filter_multiple():
    f = Filters({"ignorespaces": True, "uppercase": True, "replace": ["L", "Z"]})
    assert f("hello   world") == "HEZZOWORZD"
