from io import StringIO
from pathlib import Path

import pytest
from pydantic import ValidationError

from baygon.schema import CommonConfig, Schema, SchemaConfig


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
    assert "filters" in s.model_dump()


def test_schema_from_json():
    json_input = '{"version": 1, "tests": [{"exit": 0}]}'
    schema = Schema(json=json_input)
    config = schema.get_config()

    assert isinstance(config, SchemaConfig)
    assert config.version == 1
    assert len(config.tests) == 1
    assert config.tests[0].exit == 0


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
    assert config.tests[0].exit == 0


def test_schema_from_dict():
    dict_input = {"version": 1, "tests": [{"exit": 0}]}
    schema = Schema(various=dict_input)
    config = schema.get_config()

    assert isinstance(config, SchemaConfig)
    assert config.version == 1
    assert len(config.tests) == 1
    assert config.tests[0].exit == 0


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
    assert config.tests[0].exit == 0


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
    assert config.tests[0].exit == 0


def test_schema_from_filename(tmp_path: Path):
    import json

    fake_file = tmp_path / "fakefile.json"
    data = {"version": 1, "tests": [{"exit": 0}]}

    with fake_file.open("w") as f:
        json.dump(data, f)

    schema = Schema(filename=str(fake_file))
    config = schema.get_config()

    assert isinstance(config, SchemaConfig)
    assert config.version == 1
    assert len(config.tests) == 1
    assert config.tests[0].exit == 0


def test_invalid_version():
    invalid_input = '{"version": 3, "tests": [{"exit": 0}]}'
    with pytest.raises(ValueError, match="Only version up to 2 is accepted"):
        Schema(json=invalid_input)


def test_validate_method():
    dict_input = {"version": 1, "tests": [{"exit": 0}]}
    SchemaConfig(**dict_input)

    # Test invalid schema
    invalid_input = {"version": 3, "tests": [{"exit": 0}]}
    with pytest.raises(ValueError, match="Only version up to 2 is accepted"):
        SchemaConfig(**invalid_input)


def test_points_and_weight_conflict():
    invalid_input = {"version": 1, "points": 50, "weight": 20, "tests": [{"exit": 0}]}
    with pytest.raises(ValueError):
        SchemaConfig(**invalid_input)


def test_common_config_points_and_weight():
    # Cas où 'points' est défini sans 'weight'
    config = CommonConfig(name="test", points=10)
    assert config.points == 10
    assert config.weight is None

    # Cas où 'weight' est défini sans 'points'
    config = CommonConfig(name="test", weight=5)
    assert config.weight == 5
    assert config.points is None

    # Cas où les deux sont définis -> devrait lever une erreur
    with pytest.raises(ValueError, match="Cannot specify both 'points' and 'weight'"):
        CommonConfig(name="test", points=10, weight=5)


def test_schema_no_valid_input():
    with pytest.raises(ValueError, match="No valid input provided to build a schema."):
        Schema()


def test_schema_various_is_schema_config():
    schema_config = SchemaConfig(version=2, tests=[])
    schema = Schema(schema_config)
    assert schema.config == schema_config


def test_schema_various_is_io():
    file_like_object = StringIO('{"version": 2, "tests": []}')
    schema = Schema(file_like_object)
    assert schema.config.version == 2
    assert schema.config.tests == []


def test_schema_from_json_valid():
    json_str = '{"version": 2, "tests": []}'
    schema = Schema(json=json_str)
    assert schema.config.version == 2
    assert schema.config.tests == []


def test_schema_from_json_invalid():
    json_str = '{"version": 2, "tests": '
    with pytest.raises(ValueError, match="Invalid JSON format"):
        Schema(json=json_str)


def test_schema_from_yaml_valid():
    yaml_str = "version: 2\ntests:\n  - exit: 0"
    schema = Schema(yaml=yaml_str)
    assert schema.config.version == 2
    assert schema.config.tests[0].exit == 0


def test_schema_from_yaml_invalid():
    yaml_str = "version: 2\ntests: ["
    with pytest.raises(ValueError, match="Invalid YAML format"):
        Schema(yaml=yaml_str)


def test_schema_from_filename_file_not_found():
    with pytest.raises(ValueError, match="File 'non_existent.json' not found"):
        Schema(filename="non_existent.json")


def test_schema_validate_valid():
    schema = Schema(various={"version": 2, "tests": []})
    assert schema.config.version == 2


def test_schema_validate_invalid():
    with pytest.raises(
        ValueError,
        match="Only version up to 2 is accepted, you may used a newer schema",
    ):
        Schema(various={"version": 3, "tests": []})


def test_schema_unknown_type():
    with pytest.raises(ValueError):
        Schema(42)
