"""Unit tests targeting CLI helpers and presenters."""

# ruff: noqa: UP007

from __future__ import annotations

from io import StringIO
import json
from pathlib import Path
from typing import Optional

import pytest
from rich.console import Console
import typer
import yaml

from baygon.__main__ import (
    _format_callback,
    _version_callback,
    console as global_console,
    save_report,
)
from baygon.core.models import CaseModel, ConditionModel, SuiteModel
from baygon.presentation.rich import (
    render_command_panels,
    render_pretty_failures,
    render_summary_table,
)
from baygon.presentation.text import render_case_results, render_summary
from baygon.runtime.runner import CaseResult, CommandLog, RunReport


def _make_case(
    *,
    identifier: tuple[int, ...],
    name: str,
    points: Optional[int] = 1,
) -> CaseModel:
    return CaseModel(
        id=identifier,
        name=name,
        min_points=0.1,
        points=points,
        executable=None,
        args=(),
        env={},
        stdin="",
        stdout=(),
        stderr=(),
        repeat=1,
        exit=None,
        filters={},
    )


def _build_report() -> tuple[RunReport, CaseResult]:
    passing_case = _make_case(identifier=(1,), name="Passing", points=1)
    failing_case = _make_case(identifier=(2,), name="Failing", points=1)

    suite = SuiteModel(
        name="Example Suite",
        version=1,
        min_points=0.1,
        points=2,
        executable=None,
        filters={},
        tests=(passing_case, failing_case),
        eval=None,
        verbose=None,
        report=None,
        report_format=None,
        table=False,
        compute_score=False,
    )

    ok_result = CaseResult(
        case=passing_case,
        status="passed",
        issues=(),
        commands=(),
        duration=0.01,
        points_earned=1,
    )
    fail_result = CaseResult(
        case=failing_case,
        status="failed",
        issues=(ValueError("boom"),),
        commands=(
            CommandLog(
                argv=("prog", "arg"),
                stdin=None,
                stdout="actual",
                stderr="",
                exit_status=1,
            ),
        ),
        duration=0.02,
        points_earned=0,
    )

    report = RunReport(
        suite=suite,
        successes=1,
        failures=1,
        skipped=0,
        points_total=2,
        points_earned=1,
        duration=0.03,
        cases=(ok_result, fail_result),
    )

    return report, fail_result


def test_format_callback_normalizes_values() -> None:
    assert _format_callback("JSON") == "json"
    assert _format_callback(None) is None
    with pytest.raises(typer.BadParameter):
        _format_callback("xml")


def test_version_callback_prints_version(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(typer.Exit):
        _version_callback(True)
    out = capsys.readouterr().out
    assert "Baygon version" in out


def test_save_report_json_and_yaml(tmp_path: Path) -> None:
    data = {"alpha": 1, "beta": {"gamma": 2}}

    json_path = tmp_path / "report.json"
    save_report(data, str(json_path), "json")
    assert json.loads(json_path.read_text())["beta"]["gamma"] == 2

    yaml_path = tmp_path / "report.yaml"
    save_report(data, str(yaml_path), "yaml")
    assert yaml.safe_load(yaml_path.read_text())["alpha"] == 1


def test_text_renderer_outputs_issues() -> None:
    report, _ = _build_report()
    stream = StringIO()
    render_case_results(report, write=stream.write, verbose=1, include_issues=True)
    render_summary(report, write=stream.write)
    output = stream.getvalue()
    assert "Test 2: Failing FAILED" in output
    assert "boom" in output
    assert "Ran 2 tests in" in output
    assert "fail." in output


def test_rich_summary_table_contains_status() -> None:
    report, _ = _build_report()
    capture_console = Console(width=120, record=True)
    render_summary_table(report, console=capture_console)
    output = capture_console.export_text()
    assert "Test Summary" in output
    assert "Failing" in output
    assert "PASS" in output


def test_rich_pretty_failure_hides_empty_stdin() -> None:
    report, failing_result = _build_report()
    capture_console = Console(width=120, record=True)
    render_pretty_failures(report, console=capture_console)
    output = capture_console.export_text()
    assert f"Test {failing_result.case.id_str}: {failing_result.case.name}" in output
    assert "issues" in output
    assert "stdout" in output
    assert "Command #1" in output
    assert "stdin" not in output


def test_rich_command_panels_include_streams() -> None:
    report, failing_result = _build_report()
    capture_console = Console(width=120, record=True)
    render_command_panels(
        failing_result,
        console=capture_console,
        hide_empty_streams=False,
    )
    output = capture_console.export_text()
    assert "Command #1" in output
    assert "stdin" in output
    assert "stdout" in output
    assert "stderr" in output


def test_global_console_is_available() -> None:
    with global_console.capture() as capture:
        global_console.print("ping")
    assert "ping" in capture.get()
