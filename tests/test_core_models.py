from __future__ import annotations

from pathlib import Path

import pytest

from baygon.core.models import (
    CaseModel,
    GroupModel,
    SuiteModel,
    _as_id_tuple,
    _deep_freeze,
    build_suite_model,
)
from baygon.schema import Schema


def _load_suite_fixture(filename: str):
    config = Schema(Path("tests", filename).read_text())
    return build_suite_model(config)


def test_build_suite_model_from_schema_produces_hierarchy() -> None:
    suite = _load_suite_fixture("t.yml")

    assert suite.version == 1
    assert suite.min_points == pytest.approx(0.1)
    assert suite.compute_score is False

    groups = [node for node in suite.tests if isinstance(node, GroupModel)]
    assert len(groups) == 1
    group = groups[0]
    assert group.id == (1,)
    assert group.name == "Arguments check"
    assert len(group.tests) == 2

    cases = list(suite.iter_cases())
    assert len(cases) == 4
    assert cases[0].id == (1, 1)
    assert cases[0].args == ("1",)
    assert cases[0].stdout == ()


def test_suite_model_freezes_mappings() -> None:
    suite = _load_suite_fixture("t.yml")
    case = next(case for case in suite.iter_cases() if case.id == (2,))

    with pytest.raises(TypeError):
        case.env["NEW"] = "VALUE"  # type: ignore[index]

    with pytest.raises(TypeError):
        suite.filters["trim"] = True  # type: ignore[index]


def test_deep_freeze_handles_nested_sequences() -> None:
    frozen = _deep_freeze([{"value": [1, 2]}])
    assert isinstance(frozen, tuple)
    nested = frozen[0]["value"]
    assert isinstance(nested, tuple)


def test_as_id_tuple_handles_none() -> None:
    assert _as_id_tuple(None) == ()


def test_group_and_suite_iter_cases_nested() -> None:
    case = CaseModel(
        id=(1, 1),
        name="leaf",
        min_points=0.1,
        points=1,
        executable=None,
        args=(),
        env={},
        stdin=None,
        stdout=(),
        stderr=(),
        repeat=1,
        exit=0,
        filters={},
        eval=None,
    )
    inner_group = GroupModel(
        id=(1,),
        name="inner",
        min_points=0.1,
        points=None,
        executable=None,
        filters={},
        tests=(case,),
        eval=None,
    )
    outer_group = GroupModel(
        id=(2,),
        name="outer",
        min_points=0.1,
        points=None,
        executable=None,
        filters={},
        tests=(inner_group,),
        eval=None,
    )
    suite = SuiteModel(
        name="suite",
        version=1,
        min_points=0.1,
        points=None,
        executable=None,
        filters={},
        tests=(outer_group,),
        eval=None,
    )

    collected = list(outer_group.iter_cases())
    assert collected == [case]
    assert list(suite.iter_cases()) == [case]
