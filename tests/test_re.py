import re

import pytest

from baygon.helpers import to_pcre


def test_basic_conversion():
    regex = "s/foo/bar/gim"
    result = to_pcre(regex)
    assert result["search"] == "foo"
    assert result["replace"] == "bar"
    assert result["flags"] == re.IGNORECASE | re.MULTILINE | re.DOTALL


def test_custom_delimiter():
    regex = "s#foo#bar#gi"
    result = to_pcre(regex)
    assert result["search"] == "foo"
    assert result["replace"] == "bar"
    assert result["flags"] == re.IGNORECASE


def test_no_flags():
    regex = "s/foo/bar/"
    result = to_pcre(regex)
    assert result["search"] == "foo"
    assert result["replace"] == "bar"
    assert result["flags"] == 0


def test_invalid_flag():
    regex = "s/foo/bar/x"
    with pytest.raises(ValueError, match="Invalid flag in regex"):
        to_pcre(regex)


def test_invalid_format():
    regex = "foo/bar/gim"  # Missing 's' at the start
    with pytest.raises(ValueError, match="Regex must start with 's'"):
        to_pcre(regex)


def test_incorrect_delimiter_format():
    regex = "s/foo/bar"
    with pytest.raises(ValueError, match="Incorrect regex format"):
        to_pcre(regex)


def test_re_substitution():
    regex = "s/foo/bar/i"
    result = to_pcre(regex)
    compiled_regex = re.compile(result["search"], result["flags"])
    text = "Foo"
    replaced_text = compiled_regex.sub(result["replace"], text)
    assert replaced_text == "bar"


def test_multiline_substitution():
    regex = "s/foo/bar/m"
    result = to_pcre(regex)
    compiled_regex = re.compile(result["search"], result["flags"])
    text = "foo\nfoo"
    replaced_text = compiled_regex.sub(result["replace"], text)
    assert replaced_text == "bar\nbar"


def test_dotall_flag():
    regex = "s/./X/s"
    result = to_pcre(regex)
    compiled_regex = re.compile(result["search"], result["flags"])
    text = "foo\nbar"
    replaced_text = compiled_regex.sub(result["replace"], text)
    assert replaced_text == "XXX\nXXX"
