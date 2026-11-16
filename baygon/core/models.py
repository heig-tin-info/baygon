"""Immutable domain models for Baygon configurations and execution state."""

from __future__ import annotations

from collections.abc import Iterator, Mapping, Sequence
from copy import deepcopy
from dataclasses import dataclass, field, replace
from types import MappingProxyType
from typing import Any, Union

from baygon.score import compute_points


def _deep_freeze(value: Any) -> Any:
    """Recursively convert nested structures into immutable counterparts."""
    if isinstance(value, Mapping):
        frozen_items = {k: _deep_freeze(v) for k, v in value.items()}
        return MappingProxyType(frozen_items)
    if isinstance(value, (list, tuple)):
        return tuple(_deep_freeze(item) for item in value)
    return value


def _as_id_tuple(identifier: Sequence[int] | None) -> tuple[int, ...]:
    """Normalize hierarchical identifiers to tuples."""
    if identifier is None:
        return ()
    return tuple(int(part) for part in identifier)


@dataclass(frozen=True)
class NegatedConditionModel:
    """Single negated matcher condition."""

    equals: str | None = None
    regex: str | None = None
    contains: str | None = None


@dataclass(frozen=True)
class ConditionModel:
    """Matcher configuration applied to stdout/stderr."""

    filters: Mapping[str, Any] = field(default_factory=dict)
    equals: str | None = None
    regex: str | None = None
    contains: str | None = None
    expected: str | None = None
    negated: tuple[NegatedConditionModel, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        object.__setattr__(self, "filters", _deep_freeze(self.filters))


@dataclass(frozen=True)
class CaseModel:
    """Leaf test case definition."""

    id: tuple[int, ...]
    name: str
    min_points: float | int
    points: float | int | None
    executable: str | None
    args: tuple[str, ...]
    env: Mapping[str, str]
    stdin: str | None
    stdout: tuple[ConditionModel, ...]
    stderr: tuple[ConditionModel, ...]
    repeat: int
    exit: int | str | None
    filters: Mapping[str, Any]
    eval: Mapping[str, Any] | None = None
    timeout: float | None = None
    max_output: int | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "env", _deep_freeze(self.env))
        object.__setattr__(self, "filters", _deep_freeze(self.filters))

    @property
    def id_str(self) -> str:
        """Return the dotted identifier (e.g. '1.2.3')."""
        return ".".join(str(part) for part in self.id)


TestNode = Union["GroupModel", "CaseModel"]


@dataclass(frozen=True)
class GroupModel:
    """Hierarchical test group definition."""

    id: tuple[int, ...]
    name: str
    min_points: float | int
    points: float | int | None
    executable: str | None
    filters: Mapping[str, Any]
    tests: tuple[TestNode, ...]
    eval: Mapping[str, Any] | None = None
    timeout: float | None = None
    max_output: int | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "filters", _deep_freeze(self.filters))

    def iter_cases(self) -> Iterator[CaseModel]:
        """Iterate over every leaf case contained in this group."""
        for test in self.tests:
            if isinstance(test, CaseModel):
                yield test
            else:
                yield from test.iter_cases()


@dataclass(frozen=True)
class SuiteModel:
    """Top-level immutable suite description."""

    name: str
    version: int
    min_points: float | int
    points: float | int | None
    executable: str | None
    filters: Mapping[str, Any]
    tests: tuple[TestNode, ...]
    eval: Mapping[str, Any] | None = None
    verbose: int | None = None
    report: str | None = None
    report_format: str | None = None
    table: bool = False
    compute_score: bool = False
    timeout: float | None = None
    max_output: int | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "filters", _deep_freeze(self.filters))

    def iter_cases(self) -> Iterator[CaseModel]:
        """Iterate over every test case in the suite."""
        for test in self.tests:
            if isinstance(test, CaseModel):
                yield test
            else:
                yield from test.iter_cases()


@dataclass(frozen=True)
class ExecutionResult:
    """Lightweight execution summary for downstream reporting."""

    case: CaseModel
    status: str
    issues: tuple[Any, ...] = field(default_factory=tuple)
    duration_seconds: float | None = None
    telemetry: Mapping[str, Any] | None = None


def parse_test_id(value: str | Sequence[int]) -> tuple[int, ...]:
    """Parse a dotted test identifier.

    >>> parse_test_id("2.1")
    (2, 1)
    >>> parse_test_id(" 3 ")
    (3,)
    """
    if not isinstance(value, str):
        return _as_id_tuple(value)
    try:
        return tuple(int(part) for part in value.strip().strip(".").split("."))
    except ValueError as exc:
        raise ValueError(
            f"Invalid test id '{value}', expected e.g. '2' or '2.1'"
        ) from exc


def select_tests(
    suite: SuiteModel,
    *,
    ids: Sequence[str | Sequence[int]] | None = None,
    keywords: Sequence[str] | None = None,
) -> SuiteModel:
    """Return a copy of the suite reduced to the selected tests.

    A test is kept when its id starts with one of ``ids`` (``"2"`` keeps the
    whole group 2, ``"2.1"`` keeps test 2.1) and when its name, or the name of
    one of its groups, contains one of ``keywords`` (case insensitive). An
    empty criterion selects everything. Groups left without tests are removed,
    ids and points are kept as they are in the full suite.
    """
    id_prefixes = [parse_test_id(item) for item in ids or ()]
    words = [word.lower() for word in keywords or () if word]

    def _id_selected(node: TestNode) -> bool | None:
        if not id_prefixes:
            return True
        for prefix in id_prefixes:
            if node.id[: len(prefix)] == prefix:
                return True
        if any(prefix[: len(node.id)] == node.id for prefix in id_prefixes):
            return None  # A descendant may be selected.
        return False

    def _filter(node: TestNode, names: tuple[str, ...]) -> TestNode | None:
        names = (*names, node.name.lower())
        selected = _id_selected(node)
        if selected is False:
            return None
        if isinstance(node, CaseModel):
            if selected is None:
                return None
            if words and not any(w in name for w in words for name in names):
                return None
            return node
        children = tuple(
            child
            for child in (_filter(test, names) for test in node.tests)
            if child is not None
        )
        return replace(node, tests=children) if children else None

    tests = tuple(node for node in (_filter(test, ()) for test in suite.tests) if node)
    return replace(suite, tests=tests)


def build_suite_model(config: Mapping[str, Any]) -> SuiteModel:
    """Build an immutable `SuiteModel` from validated schema data.

    Args:
        config: Mapping returned by `baygon.schema.Schema`.

    Returns:
        SuiteModel: frozen domain representation suitable as a SSOT.
    """
    prepared = deepcopy(config)
    compute_points(prepared)
    return _build_suite(prepared)


def _build_suite(config: Mapping[str, Any]) -> SuiteModel:
    tests = tuple(_build_node(test) for test in config.get("tests", []))
    return SuiteModel(
        name=config.get("name", ""),
        version=int(config.get("version", 2)),
        min_points=config.get("min-points", 0.1),
        points=config.get("points"),
        executable=config.get("executable"),
        filters=config.get("filters", {}),
        tests=tests,
        eval=config.get("eval"),
        verbose=config.get("verbose"),
        report=config.get("report"),
        report_format=config.get("format"),
        table=config.get("table", False),
        compute_score=config.get("compute-score", False),
        timeout=config.get("timeout"),
        max_output=config.get("max-output"),
    )


def _build_node(config: Mapping[str, Any]) -> TestNode:
    if "tests" in config:
        tests = tuple(_build_node(child) for child in config.get("tests", []))
        return GroupModel(
            id=_as_id_tuple(config.get("test_id")),
            name=config.get("name", ""),
            min_points=config.get("min-points", 0.1),
            points=config.get("points"),
            executable=config.get("executable"),
            filters=config.get("filters") or {},
            tests=tests,
            eval=config.get("eval"),
            timeout=config.get("timeout"),
            max_output=config.get("max-output"),
        )
    return CaseModel(
        id=_as_id_tuple(config.get("test_id")),
        name=config.get("name", ""),
        min_points=config.get("min-points", 0.1),
        points=config.get("points"),
        executable=config.get("executable"),
        args=tuple(config.get("args") or ()),
        env=config.get("env") or {},
        stdin=config.get("stdin"),
        stdout=tuple(_build_condition(item) for item in config.get("stdout") or ()),
        stderr=tuple(_build_condition(item) for item in config.get("stderr") or ()),
        repeat=int(config.get("repeat", 1)),
        exit=config.get("exit"),
        filters=config.get("filters") or {},
        eval=config.get("eval"),
        timeout=config.get("timeout"),
        max_output=config.get("max-output"),
    )


def _build_condition(config: Mapping[str, Any]) -> ConditionModel:
    negated = tuple(
        NegatedConditionModel(
            equals=item.get("equals"),
            regex=item.get("regex"),
            contains=item.get("contains"),
        )
        for item in config.get("not") or ()
    )
    return ConditionModel(
        filters=config.get("filters") or {},
        equals=config.get("equals"),
        regex=config.get("regex"),
        contains=config.get("contains"),
        expected=config.get("expected"),
        negated=negated,
    )
