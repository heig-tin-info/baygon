"""Schema definition and validation for Baygon configurations."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Literal

import yaml
from pydantic import (
    AliasChoices,
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
    model_validator,
)

from .error import ConfigError, ConfigSyntaxError


def _coerce_value(value: Any) -> str:
    """Convert schema values to their canonical string representation."""

    if isinstance(value, bool):
        value = int(value)
    if isinstance(value, (int, float)):
        return str(value)
    return str(value)


def _coerce_match_list(value: Any) -> list[Any]:
    """Coerce the match value to a list of case dictionaries."""

    if value is None:
        return []
    if isinstance(value, (int, float, bool, str)):
        return [{"equals": _coerce_value(value)}]
    if isinstance(value, Mapping):
        return [value]
    if isinstance(value, Sequence) and not isinstance(value, str):
        items: list[Any] = []
        for item in value:
            if isinstance(item, Mapping):
                items.append(item)
            else:
                items.append({"equals": _coerce_value(item)})
        return items
    raise TypeError("Invalid match definition")


class FiltersConfig(BaseModel):
    """Filters available at the configuration or case level."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    uppercase: bool | None = None
    lowercase: bool | None = None
    trim: bool | None = None
    ignore_spaces: bool | None = Field(
        default=None,
        validation_alias=AliasChoices("ignorespaces", "ignore-spaces"),
        serialization_alias="ignorespaces",
    )
    regex: list[str] | None = None
    replace: list[str] | None = None

    @field_validator("regex", "replace", mode="before")
    @classmethod
    def _validate_pairs(cls, value: Any):
        if value is None:
            return None
        if isinstance(value, Sequence) and not isinstance(value, str) and len(value) == 2:
            return [_coerce_value(value[0]), _coerce_value(value[1])]
        raise ValueError("must be a sequence of exactly two values")


class EvalConfig(BaseModel):
    """Configuration of the Jinja-like evaluation filters."""

    model_config = ConfigDict(extra="forbid")

    start: str = "{{"
    end: str = "}}"
    init: list[str] = Field(default_factory=list)

    @field_validator("init", mode="before")
    @classmethod
    def _validate_init(cls, value: Any):
        if value is None:
            return []
        if isinstance(value, str):
            return [value]
        if isinstance(value, Sequence) and not isinstance(value, str):
            return [_coerce_value(v) for v in value]
        raise TypeError("eval.init must be a string or a list of strings")


class NegatedCondition(BaseModel):
    """Negative matcher definition."""

    model_config = ConfigDict(extra="forbid")

    equals: str | None = None
    regex: str | None = None
    contains: str | None = None

    @field_validator("equals", "regex", "contains", mode="before")
    @classmethod
    def _convert_values(cls, value: Any):
        if value is None:
            return None
        return _coerce_value(value)

    @model_validator(mode="after")
    def _ensure_single_matcher(self):
        provided = [self.equals, self.regex, self.contains]
        if sum(value is not None for value in provided) != 1:
            raise ValueError("A negated condition must define exactly one matcher")
        return self


class CaseCondition(BaseModel):
    """Matchers applied to stdout/stderr values."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    filters: FiltersConfig = Field(default_factory=FiltersConfig)
    equals: str | None = None
    regex: str | None = None
    contains: str | None = None
    expected: str | None = None
    not_conditions: list[NegatedCondition] | None = Field(default=None, alias="not")

    @field_validator("equals", "regex", "contains", "expected", mode="before")
    @classmethod
    def _convert_values(cls, value: Any):
        if value is None:
            return None
        return _coerce_value(value)

    @model_validator(mode="after")
    def _ensure_matcher(self):
        if not any([self.equals, self.regex, self.contains, self.not_conditions]):
            raise ValueError("A condition must define at least one matcher")
        return self


class CommonSettings(BaseModel):
    """Shared configuration items for suites, groups and test cases."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    name: str = ""
    executable: str | None = None
    points: float | int | None = None
    weight: float | int | None = None
    min_points: float | int = Field(0.1, alias="min-points")

    @model_validator(mode="after")
    def _check_points_weight(self):
        if self.points is not None and self.weight is not None:
            raise ValueError("'points' and 'weight' cannot be used together")
        return self


class TestCaseModel(CommonSettings):
    """Single executable test case."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    args: list[str] = Field(default_factory=list)
    env: dict[str, str] = Field(default_factory=dict)
    stdin: str | None = ""
    stdout: list[CaseCondition] = Field(default_factory=list)
    stderr: list[CaseCondition] = Field(default_factory=list)
    repeat: int = 1
    exit: int | str | bool | None = None
    test_id: list[int] = Field(default_factory=list, alias="test_id")

    @field_validator("args", mode="before")
    @classmethod
    def _convert_args(cls, value: Any):
        if value is None:
            return []
        if not isinstance(value, Sequence) or isinstance(value, str):
            raise TypeError("args must be a list")
        return [_coerce_value(item) for item in value]

    @field_validator("env", mode="before")
    @classmethod
    def _convert_env(cls, value: Any):
        if value is None:
            return {}
        if not isinstance(value, Mapping):
            raise TypeError("env must be a mapping")
        return {str(key): _coerce_value(val) for key, val in value.items()}

    @field_validator("stdin", mode="before")
    @classmethod
    def _convert_stdin(cls, value: Any):
        if value is None:
            return None
        return _coerce_value(value)

    @field_validator("stdout", "stderr", mode="before")
    @classmethod
    def _convert_matches(cls, value: Any):
        return _coerce_match_list(value)


class TestGroupModel(CommonSettings):
    """Group of tests that share settings."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    tests: list["BaygonTest"]
    test_id: list[int] = Field(default_factory=list, alias="test_id")


BaygonTest = TestCaseModel | TestGroupModel

TestGroupModel.model_rebuild()
BaygonConfig.model_rebuild()


class BaygonConfig(CommonSettings):
    """Top-level Baygon configuration."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    version: int = 2
    filters: FiltersConfig = Field(default_factory=FiltersConfig)
    tests: list[BaygonTest]
    eval: EvalConfig | None = None
    verbose: int | None = None
    report: str | None = None
    format: Literal["json", "yaml"] | None = None
    table: bool = False

    @field_validator("version", mode="before")
    @classmethod
    def _validate_version(cls, value: Any):
        if value is None:
            return 2
        if value not in {1, 2}:
            raise ValueError("version must be 1 or 2")
        return value

    @field_validator("eval", mode="before")
    @classmethod
    def _convert_eval(cls, value: Any):
        if isinstance(value, bool):
            return {"init": []}
        return value


def _assign_test_ids(tests: list[BaygonTest]) -> None:
    """Assign hierarchical identifiers to every test."""

    class _Tracker:
        def __init__(self) -> None:
            self.stack = [1]

        def current(self) -> list[int]:
            return list(self.stack)

        def increment(self) -> None:
            self.stack[-1] += 1

        def down(self) -> None:
            self.stack.append(1)

        def up(self) -> None:
            self.stack.pop()

    def _walk(items: list[BaygonTest], tracker: _Tracker) -> None:
        for item in items:
            item.test_id = tracker.current()
            if isinstance(item, TestGroupModel):
                tracker.down()
                _walk(item.tests, tracker)
                tracker.up()
            tracker.increment()

    _walk(tests, _Tracker())


def _dump_case(case: CaseCondition) -> dict[str, Any]:
    data = case.model_dump(by_alias=True, exclude_none=True, mode="python")
    return data


def _dump_test(test: BaygonTest) -> dict[str, Any]:
    if isinstance(test, TestGroupModel):
        data = test.model_dump(by_alias=True, exclude_none=True, mode="python")
        data["executable"] = test.executable
        data["tests"] = [_dump_test(child) for child in test.tests]
        return data

    data = test.model_dump(by_alias=True, exclude_none=True, mode="python")
    data["executable"] = test.executable
    data["stdout"] = [_dump_case(case) for case in test.stdout]
    data["stderr"] = [_dump_case(case) for case in test.stderr]
    return data


def _dump_config(
    config: BaygonConfig,
    *,
    include_eval: bool,
    raw_eval_value: Any,
) -> dict[str, Any]:
    data = config.model_dump(by_alias=True, exclude_none=True, mode="python")
    data["executable"] = config.executable
    data["tests"] = [_dump_test(test) for test in config.tests]

    if include_eval:
        if config.eval is None:
            eval_data = {"init": []}
        else:
            eval_data = config.eval.model_dump(by_alias=True, exclude_none=True, mode="python")
            if raw_eval_value in {True, False, None}:
                eval_data.pop("start", None)
                eval_data.pop("end", None)
            eval_data.setdefault("init", [])
        data["eval"] = eval_data

    return data


def _load_yaml(text: str) -> Mapping[str, Any]:
    try:
        loaded = yaml.safe_load(text)
    except yaml.YAMLError as exc:  # pragma: no cover - exercised in tests
        problem = getattr(exc, "problem", str(exc))
        mark = getattr(exc, "problem_mark", None)
        line = getattr(mark, "line", None)
        column = getattr(mark, "column", None)
        if line is not None:
            line += 1
        if column is not None:
            column += 1
        raise ConfigSyntaxError(problem, line=line, column=column) from exc

    if loaded is None:
        return {}
    if not isinstance(loaded, Mapping):
        raise ConfigError("Configuration root must be a mapping")
    return loaded


def _humanize_errors(error: ValidationError) -> str:
    messages: list[str] = []
    for err in error.errors():
        location = ".".join(str(part) for part in err["loc"])
        messages.append(f"{location or 'config'}: {err['msg']}")
    return "\n".join(messages)


def Schema(data: Any, humanize: bool = False):  # noqa: N802
    """Validate the given data against the Baygon schema."""

    if isinstance(data, str):
        data = _load_yaml(data)
    elif hasattr(data, "read"):
        data = _load_yaml(data.read())

    if not isinstance(data, Mapping):
        raise ConfigError("Schema expects a mapping or YAML string")

    include_eval = "eval" in data
    raw_eval_value = data.get("eval") if include_eval else None

    try:
        config = BaygonConfig.model_validate(data)
    except ValidationError as exc:  # pragma: no cover - exercised indirectly
        if humanize:
            raise ConfigError(_humanize_errors(exc)) from exc
        raise

    _assign_test_ids(config.tests)
    return _dump_config(config, include_eval=include_eval, raw_eval_value=raw_eval_value)

