from __future__ import annotations

from pathlib import Path

import pytest

from baygon.core.models import CaseModel, GroupModel, build_suite_model
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
