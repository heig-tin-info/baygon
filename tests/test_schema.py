from io import StringIO

import pytest
from pydantic import ValidationError

from baygon import Schema, SchemaConfig


def test_minimal():
    SchemaConfig(version=1, tests=[{"exit": 0}])


def test_wrong_version():
    with pytest.raises(ValidationError):
        SchemaConfig(version=3, tests=[{"exit": 0}])


def test_filters():
    SchemaConfig(
        version=1,
        filters={"uppercase": True, "ignorespaces": True},
        tests=[],
    )


def test_test_contains():
    SchemaConfig(
        version=1, tests=[{"args": ["--version"], "stderr": [{"contains": "Version"}]}]
    )


def test_empty_filters():
    s = SchemaConfig(version=1, tests=[])
    assert "filters" in s.dict()


def test_schema_from_json():
    json_input = '{"version": 1, "tests": [{"exit": 0}]}'
    schema = Schema(json=json_input)
    config = schema.get_config()

    assert isinstance(config, SchemaConfig)
    assert config.version == 1
    assert len(config.tests) == 1
    assert config.tests[0]["exit"] == 0


def test_schema_from_yaml():
    yaml_input = """
    version: 1
    tests:
      - exit: 0
    """
    schema = Schema(yaml=yaml_input)
    config = schema.get_config()

    assert isinstance(config, SchemaConfig)
    assert config.version == 1
    assert len(config.tests) == 1
    assert config.tests[0]["exit"] == 0


def test_schema_from_dict():
    dict_input = {"version": 1, "tests": [{"exit": 0}]}
    schema = Schema(various=dict_input)
    config = schema.get_config()

    assert isinstance(config, SchemaConfig)
    assert config.version == 1
    assert len(config.tests) == 1
    assert config.tests[0]["exit"] == 0


def test_invalid_string_format():
    invalid_input = "this is not valid json or yaml"
    with pytest.raises(ValueError, match="Invalid string format"):
        Schema(various=invalid_input)


def test_schema_from_file_json():
    file_input = StringIO('{"version": 1, "tests": [{"exit": 0}]}')
    schema = Schema(file=file_input)
    config = schema.get_config()

    assert isinstance(config, SchemaConfig)
    assert config.version == 1
    assert len(config.tests) == 1
    assert config.tests[0]["exit"] == 0


def test_schema_from_file_yaml():
    file_input = StringIO(
        """
    version: 1
    tests:
      - exit: 0
    """
    )
    schema = Schema(file=file_input)
    config = schema.get_config()

    assert isinstance(config, SchemaConfig)
    assert config.version == 1
    assert len(config.tests) == 1
    assert config.tests[0]["exit"] == 0


def test_schema_from_filename(mocker):
    mocker.patch(
        "builtins.open",
        mocker.mock_open(read_data='{"version": 1, "tests": [{"exit": 0}]}'),
    )
    schema = Schema(filename="fakefile.json")
    config = schema.get_config()

    assert isinstance(config, SchemaConfig)
    assert config.version == 1
    assert len(config.tests) == 1
    assert config.tests[0]["exit"] == 0


def test_invalid_version():
    invalid_input = '{"version": 3, "tests": [{"exit": 0}]}'
    with pytest.raises(ValueError, match="Only version up to 2 is accepted"):
        Schema(json=invalid_input)


def test_validate_method():
    dict_input = {"version": 1, "tests": [{"exit": 0}]}
    schema = Schema(various=dict_input)
    schema.validate()  # Should pass without any exception

    # Test invalid schema
    invalid_input = {"version": 3, "tests": [{"exit": 0}]}
    schema = Schema(various=invalid_input)
    with pytest.raises(ValueError, match="Only version up to 2 is accepted"):
        schema.validate()


def test_points_and_weight_conflict():
    invalid_input = {"version": 1, "points": 50, "weight": 20, "tests": [{"exit": 0}]}
    with pytest.raises(ValueError, match="Cannot specify both 'points' and 'weight'"):
        Schema(various=invalid_input)
