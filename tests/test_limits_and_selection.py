"""Timeouts, output limits, test selection and detailed reports."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import sys
from typing import Any

from pydantic import ValidationError
import pytest

from baygon.core.models import build_suite_model, parse_test_id, select_tests
from baygon.executable import DEFAULT_MAX_OUTPUT, Executable, Outputs
from baygon.filters import Filters
from baygon.matchers import (
    ExecutionFailed,
    ExecutionTimeout,
    MatchContains,
    MatchEquals,
    MatchRegex,
    OutputLimitExceeded,
)
from baygon.runtime.runner import BaygonRunner
from baygon.schema import Schema
from baygon.suite import SuiteExecutor, SuiteLoader, SuiteService


def _suite(data: dict[str, Any]):
    return build_suite_model(Schema({"version": 1, **data}))


@dataclass
class RecordingExecutable:
    """Fake program that records the keyword arguments of each run."""

    path: str
    calls: list[dict[str, Any]]
    outputs: dict[str, Outputs] = field(default_factory=dict)

    def run(self, *args: str, **kwargs: Any) -> Outputs:
        self.calls.append({"path": self.path, "args": args, **kwargs})
        output = self.outputs.get(args[0] if args else "", Outputs(0, "", ""))
        if kwargs.get("hook"):
            kwargs["hook"](
                cmd=[self.path, *args],
                stdin=kwargs.get("stdin"),
                stdout=output.stdout,
                stderr=output.stderr,
                exit_status=output.exit_status,
            )
        return output


def _recording_factory(calls, outputs=None):
    def _factory(path: str) -> RecordingExecutable:
        return RecordingExecutable(path=path, calls=calls, outputs=outputs or {})

    return _factory


# --- Schema -----------------------------------------------------------------


def test_schema_accepts_limits_at_every_level() -> None:
    config = Schema(
        {
            "version": 1,
            "timeout": 5,
            "max-output": "1M",
            "tests": [
                {"name": "a", "timeout": 0.5, "max-output": 1024},
                {"name": "g", "timeout": 2, "tests": [{"name": "b"}]},
            ],
        }
    )
    assert config["timeout"] == 5
    assert config["max-output"] == 1024 * 1024
    assert config["tests"][0]["timeout"] == 0.5
    assert config["tests"][0]["max-output"] == 1024
    assert config["tests"][1]["timeout"] == 2
    assert "timeout" not in config["tests"][1]["tests"][0]


def test_schema_without_limits_is_unchanged() -> None:
    config = Schema({"version": 1, "tests": [{"name": "a"}]})
    assert "timeout" not in config
    assert "max-output" not in config


@pytest.mark.parametrize("value", [0, -1, "5", True])
def test_schema_rejects_invalid_timeout(value) -> None:
    with pytest.raises(ValidationError):
        Schema({"version": 1, "timeout": value, "tests": []})


@pytest.mark.parametrize(
    ("value", "expected"),
    [(0, 0), (10, 10), ("10k", 10240), ("2 MB", 2 * 1024**2), ("1GiB", 1024**3)],
)
def test_schema_parses_sizes(value, expected) -> None:
    config = Schema({"version": 1, "max-output": value, "tests": []})
    assert config["max-output"] == expected


@pytest.mark.parametrize("value", ["lots", -5, True, [1]])
def test_schema_rejects_invalid_sizes(value) -> None:
    with pytest.raises(ValidationError):
        Schema({"version": 1, "max-output": value, "tests": []})


# --- Runner -----------------------------------------------------------------


def test_limits_are_inherited_and_overridden(tmp_path: Path) -> None:
    suite = _suite(
        {
            "executable": "prog",
            "timeout": 5,
            "max-output": 100,
            "tests": [
                {"name": "suite default", "args": ["a"]},
                {"name": "own", "args": ["b"], "timeout": 1, "max-output": 0},
                {
                    "name": "group",
                    "timeout": 2,
                    "tests": [
                        {"name": "from group", "args": ["c"]},
                        {"name": "nearest", "args": ["d"], "timeout": 0.5},
                    ],
                },
            ],
        }
    )
    calls: list[dict[str, Any]] = []
    BaygonRunner(
        suite, base_dir=tmp_path, executable_factory=_recording_factory(calls)
    ).run()

    limits = [(call["timeout"], call["max_output"]) for call in calls]
    assert limits == [(5, 100), (1, 0), (2, 100), (0.5, 100)]


def test_runner_default_timeout_only_fills_gaps(tmp_path: Path) -> None:
    suite = _suite(
        {
            "executable": "prog",
            "tests": [{"args": ["a"]}, {"args": ["b"], "timeout": 1}],
        }
    )
    calls: list[dict[str, Any]] = []
    BaygonRunner(
        suite,
        base_dir=tmp_path,
        executable_factory=_recording_factory(calls),
        timeout=9,
        max_output=50,
    ).run()
    assert [call["timeout"] for call in calls] == [9, 1]
    assert [call["max_output"] for call in calls] == [50, 50]


def test_limits_are_not_passed_when_unset(tmp_path: Path) -> None:
    """A custom executable that does not know the limits keeps working."""

    class Legacy:
        def run(self, *args, stdin=None, env=None, hook=None):
            return Outputs(0, "", "")

    suite = _suite({"executable": "prog", "tests": [{"name": "a"}]})
    report = BaygonRunner(
        suite, base_dir=tmp_path, executable_factory=lambda _path: Legacy()
    ).run()
    assert report.successes == 1


def test_timeout_fails_only_that_test(tmp_path: Path) -> None:
    suite = _suite(
        {
            "executable": "prog",
            "timeout": 1,
            "tests": [
                {"name": "hangs", "args": ["hang"], "repeat": 3, "stdout": "x"},
                {"name": "fine", "args": ["ok"], "stdout": "ok"},
            ],
        }
    )
    calls: list[dict[str, Any]] = []
    outputs = {
        "hang": Outputs(-9, "partial", "", timed_out=True),
        "ok": Outputs(0, "ok", ""),
    }
    report = BaygonRunner(
        suite,
        base_dir=tmp_path,
        executable_factory=_recording_factory(calls, outputs),
    ).run()

    hang, fine = report.cases
    assert hang.status == "failed"
    assert [str(issue) for issue in hang.issues] == ["Timeout after 1 s."]
    assert isinstance(hang.issues[0], ExecutionTimeout)
    assert hang.commands[0].timed_out is True
    assert len([c for c in calls if c["args"] == ("hang",)]) == 1  # no repeat
    assert fine.status == "passed"


def test_output_limit_fails_the_test(tmp_path: Path) -> None:
    suite = _suite({"executable": "prog", "tests": [{"args": ["loop"]}]})
    outputs = {"loop": Outputs(-9, "menu\n" * 10, "", output_limit_exceeded=True)}
    report = BaygonRunner(
        suite,
        base_dir=tmp_path,
        executable_factory=_recording_factory([], outputs),
    ).run()
    (case,) = report.cases
    assert case.status == "failed"
    assert isinstance(case.issues[0], OutputLimitExceeded)
    assert str(DEFAULT_MAX_OUTPUT) in str(case.issues[0])
    assert case.commands[0].output_limit_exceeded is True


def test_program_that_cannot_start_fails_alone(tmp_path: Path) -> None:
    script = tmp_path / "noshebang"
    script.write_text("echo hi\n", encoding="utf-8")
    script.chmod(0o755)
    suite = _suite(
        {
            "tests": [
                {"name": "broken", "executable": str(script)},
                {"name": "fine", "executable": sys.executable, "args": ["-c", ""]},
            ],
        }
    )

    class Failing(Executable):
        def run(self, *args, **kwargs):
            if self.filename == str(script):
                raise OSError(8, "Exec format error")
            return super().run(*args, **kwargs)

    report = BaygonRunner(suite, base_dir=tmp_path, executable_factory=Failing).run()
    broken, fine = report.cases
    assert broken.status == "failed"
    assert isinstance(broken.issues[0], ExecutionFailed)
    assert "Exec format error" in str(broken.issues[0])
    assert fine.status == "passed"


def test_real_hanging_program_with_timeout(tmp_path: Path) -> None:
    suite = _suite(
        {
            "executable": sys.executable,
            "tests": [
                {"name": "hangs", "args": ["-c", "while True: pass"], "timeout": 0.3},
                {"name": "prints", "args": ["-c", "while True: print(1)"]},
                {"name": "ok", "args": ["-c", "print(1)"], "stdout": "1\n"},
            ],
        }
    )
    report = BaygonRunner(suite, base_dir=tmp_path, timeout=30, max_output=4096).run()
    assert [case.status for case in report.cases] == ["failed", "failed", "passed"]
    assert isinstance(report.cases[0].issues[0], ExecutionTimeout)
    assert isinstance(report.cases[1].issues[0], OutputLimitExceeded)


# --- Selection --------------------------------------------------------------

SELECTION = {
    "executable": "prog",
    "tests": [
        {"name": "Alpha", "points": 2},
        {
            "name": "CDC-2 parsing",
            "tests": [
                {"name": "empty", "points": 1},
                {"name": "full", "points": 3},
                {"name": "deep", "tests": [{"name": "leaf", "points": 4}]},
            ],
        },
        {"name": "Omega", "points": 5},
    ],
}


def _ids(suite) -> list[str]:
    return [case.id_str for case in suite.iter_cases()]


def test_parse_test_id() -> None:
    assert parse_test_id("2.1.") == (2, 1)
    assert parse_test_id([1, 2]) == (1, 2)
    with pytest.raises(ValueError, match="Invalid test id"):
        parse_test_id("two")


def test_select_by_id() -> None:
    suite = _suite(SELECTION)
    assert _ids(select_tests(suite, ids=["2"])) == ["2.1", "2.2", "2.3.1"]
    assert _ids(select_tests(suite, ids=["2.3.1", "3"])) == ["2.3.1", "3"]
    assert _ids(select_tests(suite, ids=["1.1"])) == []
    assert _ids(select_tests(suite, ids=["9"])) == []
    assert _ids(select_tests(suite)) == _ids(suite)


def test_select_by_keyword_matches_groups() -> None:
    suite = _suite(SELECTION)
    assert _ids(select_tests(suite, keywords=["cdc-2"])) == ["2.1", "2.2", "2.3.1"]
    assert _ids(select_tests(suite, keywords=["FULL", "omega"])) == ["2.2", "3"]
    assert _ids(select_tests(suite, ids=["2"], keywords=["leaf"])) == ["2.3.1"]


def test_selection_counts_only_selected_points(tmp_path: Path) -> None:
    loader = SuiteLoader()
    context = loader.from_mapping({"version": 1, **SELECTION}, cwd=tmp_path)
    selected = context.select(ids=["2"])
    report = SuiteExecutor(
        runner_factory=lambda model, **kw: BaygonRunner(
            model, executable_factory=_recording_factory([]), **kw
        )
    ).run(selected)
    assert report.total == 3
    assert report.points_total == 8
    assert report.points_earned == 8


def test_report_details(tmp_path: Path) -> None:
    outputs = {"fail": Outputs(1, "", "")}
    suite = _suite(
        {
            **SELECTION,
            "tests": [
                *SELECTION["tests"][:2],
                {"name": "Omega", "points": 5, "args": ["fail"], "exit": 0},
            ],
        }
    )
    report = BaygonRunner(
        suite,
        base_dir=tmp_path,
        executable_factory=_recording_factory([], outputs),
    ).run()
    payload = report.as_dict()

    assert payload["points"] == {"total": 15, "earned": 10}
    assert [case["id"] for case in payload["cases"]] == [
        "1",
        "2.1",
        "2.2",
        "2.3.1",
        "3",
    ]
    omega = payload["cases"][-1]
    assert omega["status"] == "failed"
    assert omega["points"] == {"total": 5, "earned": 0}
    assert omega["issues"] == ["Invalid exit status: expected 0, got 1."]
    groups = {group["id"]: group for group in payload["groups"]}
    assert groups["2"]["points"] == {"total": 8, "earned": 8}
    assert groups["2"]["total"] == 3
    assert groups["2.3"]["name"] == "deep"
    assert "cases" not in report.as_dict(details=False)


def test_service_passes_timeout(tmp_path: Path) -> None:
    received: dict[str, Any] = {}

    def _factory(model, **kwargs):
        received.update(kwargs)
        return BaygonRunner(model, executable_factory=_recording_factory([]), **kwargs)

    service = SuiteService(executor=SuiteExecutor(runner_factory=_factory))
    service.run(
        data={"version": 1, "executable": "p", "tests": [{"name": "a"}]},
        cwd=tmp_path,
        timeout=3,
        max_output=10,
    )
    assert received["timeout"] == 3
    assert received["max_output"] == 10


# --- Matchers and filters ---------------------------------------------------


def test_negated_matchers_explain_the_failure() -> None:
    contains = MatchContains("warning:", inverse=True)("x warning: y", on="stdout")
    assert (
        str(contains)
        == 'Output stdout should not contain warning:. Found "x warning: y".'
    )
    regex = MatchRegex("w.rn", inverse=True)("warn", on="stdout")
    assert "should not match /w.rn/" in str(regex)
    equals = MatchEquals("a", inverse=True)("a", on="stdout")
    assert str(equals) == "Output 'a' should not equal 'a' on stdout."
    assert "does not contain" in str(MatchContains("z")("abc", on="stdout"))


def test_disabled_filters_are_not_applied() -> None:
    filters = Filters({"uppercase": False, "ignorespaces": False, "trim": True})
    assert filters(" a b ") == "a b"
