"""Feedback for students: custom messages, first failing run, readable diffs."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import os
from pathlib import Path
from typing import Any

from pydantic import ValidationError
import pytest
from rich.console import Console

from baygon import eval as baygon_eval
from baygon.core.models import build_suite_model
from baygon.executable import Outputs
from baygon.helpers import display_command, display_program
from baygon.matchers import describe_difference
from baygon.presentation.rich import render_pretty_failures
from baygon.presentation.text import failure_details, render_case_results
from baygon.runtime.runner import BaygonRunner, CaseResult
from baygon.schema import Schema

Program = Callable[[tuple[str, ...], str | None], tuple[int, str, str]]


@dataclass
class FakeExecutable:
    """Runs a Python function instead of a program, and logs every call."""

    path: str
    program: Program
    calls: list[tuple[str, ...]]

    def run(
        self,
        *args: str,
        stdin: str | None = None,
        env: dict[str, Any] | None = None,
        hook: Callable[..., None] | None = None,
        **limits: Any,
    ) -> Outputs:
        self.calls.append(tuple(args))
        exit_status, stdout, stderr = self.program(tuple(args), stdin)
        if hook:
            hook(
                cmd=[self.path, *args],
                stdin=stdin,
                stdout=stdout,
                stderr=stderr,
                exit_status=exit_status,
            )
        return Outputs(exit_status=exit_status, stdout=stdout, stderr=stderr)


@pytest.fixture(autouse=True)
def _reset_counters() -> None:
    """``iter()`` counters are global: start each test from scratch."""
    baygon_eval.reset()


def _run(config: dict[str, Any], program: Program, tmp_path: Path):
    calls: list[tuple[str, ...]] = []
    suite = build_suite_model(Schema({"version": 1, **config}))
    runner = BaygonRunner(
        suite,
        base_dir=tmp_path,
        executable=str(tmp_path / "prog"),
        executable_factory=lambda path: FakeExecutable(path, program, calls),
    )
    return runner.run(), calls


def _double(args: tuple[str, ...], stdin: str | None) -> tuple[int, str, str]:
    """Doubles its argument, but gets 3 wrong."""
    number = int(args[0])
    return 0, f"{number * 2 + (number == 3)}\n", ""


def _exit_one(args: tuple[str, ...], stdin: str | None) -> tuple[int, str, str]:
    return 1, "usage: prog NUMBER\n", ""


# ------------------------------------------------------------------ repeat


def test_repeat_stops_at_the_first_failing_run(tmp_path: Path) -> None:
    report, calls = _run(
        {
            "eval": True,
            "tests": [
                {
                    "name": "Doubles",
                    "repeat": 10,
                    "args": ["{{ n = iter(1) }}"],
                    "stdout": "{{ 2 * n }}\n",
                }
            ],
        },
        _double,
        tmp_path,
    )
    result = report.cases[0]
    assert calls == [("1",), ("2",), ("3",)]
    assert result.status == "failed"
    assert result.failed_run == 3
    assert len(result.issues) == 1
    assert report.as_dict()["cases"][0]["failed_run"] == 3


def test_repeat_runs_every_time_when_all_pass(tmp_path: Path) -> None:
    report, calls = _run(
        {"tests": [{"repeat": 4, "args": [2], "stdout": "4\n"}]},
        _double,
        tmp_path,
    )
    assert len(calls) == 4
    assert report.cases[0].failed_run is None
    assert "failed_run" not in report.as_dict()["cases"][0]


# ---------------------------------------------------------------- messages


def test_test_message_is_evaluated_with_the_failing_values(tmp_path: Path) -> None:
    report, _ = _run(
        {
            "eval": True,
            "tests": [
                {
                    "repeat": 5,
                    "args": ["{{ n = iter(1) }}"],
                    "stdout": "{{ 2 * n }}\n",
                    "message": "The double of {{ n }} is {{ 2 * n }}.",
                }
            ],
        },
        _double,
        tmp_path,
    )
    result = report.cases[0]
    assert result.message == "The double of 3 is 6."
    assert result.messages == ["The double of 3 is 6."]
    assert report.as_dict()["cases"][0]["messages"] == ["The double of 3 is 6."]


def test_group_message_is_inherited_unless_overridden(tmp_path: Path) -> None:
    report, _ = _run(
        {
            "tests": [
                {
                    "name": "Errors",
                    "message": "main must return 2.",
                    "tests": [
                        {"args": ["x"], "exit": 2},
                        {"args": ["y"], "exit": 2, "message": "Own message."},
                    ],
                }
            ]
        },
        _exit_one,
        tmp_path,
    )
    assert [r.message for r in report.cases] == ["main must return 2.", "Own message."]


def test_message_is_not_set_on_success(tmp_path: Path) -> None:
    report, _ = _run(
        {"tests": [{"args": [2], "stdout": "4\n", "message": "Never shown."}]},
        _double,
        tmp_path,
    )
    assert report.cases[0].message is None
    assert "messages" not in report.as_dict()["cases"][0]


def test_condition_message_explains_its_own_issues(tmp_path: Path) -> None:
    report, _ = _run(
        {
            "tests": [
                {
                    "args": [3],
                    "stdout": [
                        {"lines": 1, "message": "One line only."},
                        {"equals": "6\n", "message": "3 times 2 is 6."},
                    ],
                }
            ]
        },
        _double,
        tmp_path,
    )
    (issue,) = report.cases[0].issues
    assert issue.message == "3 times 2 is 6."
    assert report.cases[0].messages == ["3 times 2 is 6."]


def test_exit_message(tmp_path: Path) -> None:
    report, _ = _run(
        {
            "tests": [
                {
                    "args": ["abc"],
                    "exit": {"value": 2, "message": "Use return 2; in main."},
                    "stdout": [{"contains": "usage", "message": "Unused."}],
                }
            ]
        },
        _exit_one,
        tmp_path,
    )
    (issue,) = report.cases[0].issues
    assert str(issue) == "Invalid exit status: expected 2, got 1."
    assert issue.message == "Use return 2; in main."


def test_exit_mapping_reads_booleans_and_needs_a_value() -> None:
    config = Schema({"tests": [{"exit": {"value": True}}]})
    assert build_suite_model(config).tests[0].exit == 1
    with pytest.raises(ValidationError):
        Schema({"tests": [{"exit": {"message": "no value"}}]})


def test_message_alone_is_not_a_condition() -> None:
    with pytest.raises(ValidationError):
        Schema({"tests": [{"stdout": [{"message": "nothing to check"}]}]})


def test_invalid_expression_in_a_message_is_reported(tmp_path: Path) -> None:
    report, _ = _run(
        {
            "eval": True,
            "tests": [{"args": [3], "stdout": "6\n", "message": "{{ unknown }}"}],
        },
        _double,
        tmp_path,
    )
    result = report.cases[0]
    assert result.message == "{{ unknown }}"
    assert any("Invalid test" in str(issue) for issue in result.issues)


# -------------------------------------------------------------- rendering


def _failing_result(tmp_path: Path) -> CaseResult:
    report, _ = _run(
        {
            "eval": True,
            "tests": [
                {
                    "name": "Doubles",
                    "repeat": 5,
                    "args": ["{{ n = iter(1) }}"],
                    "stdout": [
                        {"equals": "{{ 2 * n }}\n", "message": "Wrong double."},
                    ],
                    "message": "Check the double of {{ n }}.",
                }
            ],
        },
        _double,
        tmp_path,
    )
    return report.cases[0]


def test_text_shows_command_messages_and_issue(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    result = _failing_result(tmp_path)
    assert failure_details(result) == [
        "$ ./prog 3  # run 3 of 5",
        "Check the double of 3.",
        "Wrong double.",
        "Output stdout differs from the expected output on line 1:",
        "  expected: '6'",
        "  found:    '7'",
    ]

    lines: list[str] = []
    report = type("Report", (), {"cases": (result,)})()
    render_case_results(report, write=lines.append)
    assert lines[0] == "Test 1: Doubles FAILED"
    assert lines[1] == "    $ ./prog 3  # run 3 of 5"


def test_text_without_command(tmp_path: Path) -> None:
    result = _failing_result(tmp_path)
    bare = CaseResult(
        case=result.case,
        status="failed",
        issues=result.issues,
        commands=(),
        message=None,
    )
    assert bare.command is None
    assert failure_details(bare)[0] == "Wrong double."


def test_pretty_panel_shows_run_and_messages(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    result = _failing_result(tmp_path)
    console = Console(width=120, record=True)
    report = type("Report", (), {"cases": (result,)})()
    render_pretty_failures(report, console=console)
    output = console.export_text()
    assert "3 of 5" in output
    assert "Check the double of 3." in output
    assert "Wrong double." in output
    assert "./prog 3" in output


# ------------------------------------------------------------ differences


@pytest.mark.parametrize(
    ("expected", "found", "text"),
    [
        ("a", "a\n", "there is an extra newline at the end"),
        ("a\r\n", "a\n", "the line endings differ"),
        ("a\n", "a\nb\n", "expected: (end of output)\n  found:    'b'"),
    ],
)
def test_describe_difference(expected: str, found: str, text: str) -> None:
    assert text in describe_difference("stdout", expected, found)


def test_long_lines_are_cut_around_the_difference() -> None:
    expected = " -> ".join(str(n) for n in range(200)) + "\n"
    found = expected.replace("150", "15O")
    message = describe_difference("stdout", expected, found)
    want, got = (line.split(": ", 1)[1] for line in message.splitlines()[1:])
    assert "150" in want and "15O" in got
    assert want.startswith("'…") and want.endswith("…'")
    assert len(want) < 80


# ---------------------------------------------------------------- helpers


def test_display_program_on_another_drive(monkeypatch: pytest.MonkeyPatch) -> None:
    def _relpath(path: str, start: str | None = None) -> str:
        raise ValueError("path is on mount 'D:', start on mount 'C:'")

    monkeypatch.setattr(os.path, "relpath", _relpath)
    assert display_program("/abs/prog") == "/abs/prog"


def test_display_command_edge_cases() -> None:
    assert display_command([]) == []
    lines = display_command(["/lab/prog"], stdin="x\n" * 15, start="/lab")
    assert lines[0] == "$ ./prog <<'EOF'"
    assert lines[-2] == "... (5 more lines)"
    assert lines[-1] == "EOF"
