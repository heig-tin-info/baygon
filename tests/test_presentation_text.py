from __future__ import annotations

from baygon.core.models import CaseModel
from baygon.presentation import text as text_presentation
from baygon.runtime.runner import CaseResult, RunReport


def _case(name: str, status: str, issues=None) -> CaseResult:
    case = CaseModel(
        id=(1,),
        name=name,
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
    return CaseResult(
        case=case,
        status=status,
        issues=tuple(issues or ()),
        commands=(),
        points_earned=1 if status == "passed" else 0,
    )


def test_render_case_results_variants() -> None:
    output: list[str] = []
    results = (
        _case("pass", "passed"),
        _case("fail", "failed", issues=["broken"]),
        _case("skip", "skipped"),
        _case("other", "UNKNOWN"),
    )
    report = RunReport(
        suite=None,  # type: ignore[arg-type]
        successes=1,
        failures=1,
        skipped=1,
        points_total=4,
        points_earned=1,
        duration=0.1,
        cases=results,
    )

    text_presentation.render_case_results(
        report, write=output.append, include_issues=False
    )
    assert any("PASSED" in line for line in output)
    assert any("FAILED" in line for line in output)
    assert any("SKIPPED" in line for line in output)
    assert any("UNKNOWN" in line for line in output)


def test_render_summary_reports_points_and_failures() -> None:
    output: list[str] = []
    report = RunReport(
        suite=None,  # type: ignore[arg-type]
        successes=1,
        failures=1,
        skipped=1,
        points_total=10,
        points_earned=4,
        duration=0.54321,
        cases=(),
    )

    text_presentation.render_summary(report, write=output.append)
    assert any("Ran 3 tests" in line for line in output)
    assert any("Points: 4/10" in line for line in output)
    assert any("1 failed" in line for line in output)
    assert any("1 test(s) skipped" in line for line in output)
