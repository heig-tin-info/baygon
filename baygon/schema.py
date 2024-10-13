import json
from io import StringIO
from typing import IO, Any, Dict, List, Literal, Optional, Union
from pathlib import Path, PosixPath
import yaml
from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator

Value = Union[str, int, float, bool]


class MinPointsMixin:
    min_points: float = Field(0.1, alias="min-points")


class EnvMixin:
    timeout: Optional[int] = None
    use_tty: Optional[bool] = False
    env: Dict[str, Value] = {}


class CLIMixin:
    """CLI configuration that can be overridden by CLI arguments"""

    verbose: Optional[int] = 0
    report: Optional[str] = None
    format: Optional[Literal["json", "yaml"]] = "json"
    table: bool = False


class EvaluateConfig(BaseModel):
    start: str = "{{"
    end: str = "}}"
    init: Optional[List[str]] = None


class FiltersConfig(BaseModel):
    uppercase: Optional[bool] = None
    lowercase: Optional[bool] = None
    trim: Optional[bool] = None
    ignorespaces: Optional[bool] = Field(None, alias="ignore-spaces")
    regex: Optional[List[str]] = None
    replace: Optional[List[str]] = None


class CaseConfig(BaseModel):
    filters: FiltersConfig = FiltersConfig()
    equals: Optional[Value] = None
    regex: Optional[Value] = None
    contains: Optional[Value] = None
    negate: Optional[List[Dict[str, Value]]] = None
    expected: Optional[Value] = None


class CommonConfig(BaseModel, MinPointsMixin, EnvMixin):
    name: str = ""
    executable: Optional[str] = None
    points: Optional[float] = None
    weight: Optional[float] = None

    @model_validator(mode="before")
    def check_points_and_weight(cls, values):
        points = values.get("points")
        weight = values.get("weight")
        if points is not None and weight is not None:
            raise ValueError("Cannot specify both 'points' and 'weight'")
        return values


class TestConfig(CommonConfig):
    args: List[Value] = []
    stdin: Optional[Value] = ""
    stdout: Optional[List[Union[Value, "CaseConfig"]]] = []
    stderr: Optional[List[Union[Value, "CaseConfig"]]] = []
    repeat: int = 1
    exit: Optional[Union[int, str, bool]] = None


class GroupConfig(CommonConfig):
    tests: List[Union["GroupConfig", TestConfig]]

    model_config = {"arbitrary_types_allowed": True}


GroupConfig.model_rebuild()


class SchemaConfig(BaseModel, CLIMixin, MinPointsMixin, EnvMixin):
    name: Optional[str] = None
    version: int = 2
    filters: FiltersConfig = FiltersConfig()
    tests: List[Union[GroupConfig, TestConfig]]
    points: Optional[float] = None
    evaluate: Optional[EvaluateConfig] = None

    @model_validator(mode="before")
    def check_forbidden_fields(cls, values):
        if "weight" in values:
            raise ValueError("The field 'weight' is not allowed in SchemaConfig.")
        return values

    @field_validator("version")
    def _check_version(cls, v):
        if v > 2:
            raise ValueError(
                "Only version up to 2 is accepted, you may used a newer schema"
            )
        return v

    model_config = {"populate_by_name": True}  # Remplace l'ancienne classe Config


class Schema:
    def __init__(self, various=None, json=None, yaml=None, file=None, filename=None):
        """
        Initialize the schema based on the input provided. It will parse and validate
        the input into a SchemaConfig model.
        """

        if various:
            if isinstance(various, (PosixPath, Path)):
                self.config = self._from_filename(various)
            else:
                self.config = self._from_various(various)
        elif json:
            self.config = self._from_json(json)
        elif yaml:
            self.config = self._from_yaml(yaml)
        elif file:
            self.config = self._from_file(file)
        elif filename:
            self.config = self._from_filename(filename)
        else:
            raise ValueError("No valid input provided to build a schema.")

    def _from_various(self, various: Any) -> SchemaConfig:
        if isinstance(various, SchemaConfig):
            return various
        elif isinstance(various, dict):
            return SchemaConfig(**various)
        elif isinstance(various, str):
            try:
                # Attempt to parse as JSON
                return self._from_json(various)
            except ValueError:
                try:
                    # Attempt to parse as YAML
                    return self._from_yaml(various)
                except ValueError:
                    raise ValueError("Invalid string format. Must be JSON or YAML.")
        elif isinstance(various, StringIO):
            return self._from_various(various.getvalue())
        else:
            raise ValueError("Unsupported input type for `various`.")

    def _from_json(self, json_str: str) -> SchemaConfig:
        """
        Parse the input as JSON and return a validated SchemaConfig.
        """
        if not isinstance(json_str, str):
            raise ValueError("Not a string")

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {e}")

        return SchemaConfig(**data)

    def _from_yaml(self, yaml_str: str) -> SchemaConfig:
        """
        Parse the input as YAML and return a validated SchemaConfig.
        """
        try:
            data = yaml.safe_load(yaml_str)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML format: {e}")
        if not isinstance(data, dict):
            raise ValueError("Malformed YAML.")
        return SchemaConfig(**data)

    def _from_file(self, file: IO) -> SchemaConfig:
        """
        Read and parse a file-like object (can be JSON or YAML).
        """
        content = file.read()
        return self._from_various(content)

    def _from_filename(self, filename: str) -> SchemaConfig:
        """
        Open and parse a file (can be JSON or YAML).
        """
        try:
            with open(filename, "r") as f:
                content = f.read()
                return self._from_various(content)
        except FileNotFoundError:
            raise ValueError(f"File '{filename}' not found.")
        except IOError as e:
            raise ValueError(f"Error reading file '{filename}': {e}")

    def validate(self) -> None:
        """
        Validate the schema using Pydantic validation.
        If the schema is invalid, a ValidationError will be raised.
        """
        try:
            self.config = SchemaConfig(**self.config)
        except ValidationError as e:
            raise ValueError(f"Schema validation failed: {e}")

    def get_config(self) -> SchemaConfig:
        """
        Return the validated SchemaConfig.
        """
        return self.config
