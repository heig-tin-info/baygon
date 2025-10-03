from io import StringIO
from pathlib import Path

import pytest
from voluptuous import Invalid

from baygon.schema import SchemaConfig


def test_minimal():
    result = SchemaConfig({"version": 1, "tests": [{"exit": 0}]})
    assert result["version"] == 1


def test_wrong_version():
    with pytest.raises(Invalid):
        SchemaConfig({"version": 3, "tests": [{"exit": 0}]})


def test_filters():
    result = SchemaConfig({
        "version": 1,
        "filters": {"uppercase": True, "ignorespaces": True},
        "tests": [],
    })
    assert result["filters"]["uppercase"] is True


def test_test_contains():
    result = SchemaConfig({
        "version": 1, "tests": [{"args": ["--version"], "stderr": [{"contains": "Version"}]}]
    })
    assert len(result["tests"]) == 1


def test_empty_filters():
    s = SchemaConfig({"version": 1, "tests": []})
    assert "filters" in s


def test_invalid_version():
    with pytest.raises(Invalid):
        SchemaConfig({"version": 3, "tests": [{"exit": 0}]})


def test_points_test():
    result = SchemaConfig({"version": 1, "points": 50, "tests": [{"exit": 0}]})
    assert result["points"] == 50
