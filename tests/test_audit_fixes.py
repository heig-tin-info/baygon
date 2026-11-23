"""Regressions found by the code audit."""

from __future__ import annotations

from pathlib import Path
import shutil
import sys

from pydantic import ValidationError
import pytest
from typer.testing import CliRunner
import yaml

from baygon.__main__ import app
from baygon.core.models import build_suite_model
from baygon.filters import FilterEval
from baygon.matchers import InvalidTestDefinition
from baygon.runtime.runner import BaygonRunner, _round_points
from baygon.schema import Schema, _humanize_errors
from baygon.suite import SuiteService

HERE = Path(__file__).resolve().parent


def test_eval_given_as_a_mapping() -> None:
    config = Schema(
        {
            "version": 1,
            "eval": {"start": "<<", "end": ">>", "init": "x = 1"},
            "tests": [],
        }
    )
    assert config["eval"] == {"start": "<<", "end": ">>", "init": ["x = 1"]}


def test_eval_false_disables_eval() -> None:
    assert "eval" not in Schema({"version": 1, "eval": False, "tests": []})
    assert Schema({"version": 1, "eval": True, "tests": []})["eval"] == {"init": []}


@pytest.mark.skipif(shutil.which("perl") is None, reason="perl is required")
def test_eval_example_file_runs() -> None:
    report = SuiteService().run(path=HERE / "eval.yml")
    assert report.failures == 0, [str(i) for c in report.cases for i in c.issues]
    assert report.successes == 4


def test_iter_keeps_one_counter_per_mustache() -> None:
    f = FilterEval()
    assert [f("{{iter()}}") for _ in range(3)] == ["0", "1", "2"]
    assert [f("{{iter(10, 5)}}") for _ in range(2)] == ["10", "15"]
    assert f("{{ iter(int(5), 1) }}") == "5"
    assert f("{{ iter(ctx='k') }}") == "0"


def test_eval_delimiters_are_literal() -> None:
    assert FilterEval(start="[[", end="]]")("a [[ 1 + 1 ]] b") == "a 2 b"
    assert FilterEval(start="$(", end=")")("a $( 2 * 3 ) b") == "a 6 b"


def test_empty_output_can_be_asserted() -> None:
    config = Schema(
        {"version": 1, "tests": [{"stdout": ""}, {"stderr": [{"contains": ""}]}]}
    )
    assert config["tests"][0]["stdout"] == [{"filters": {}, "equals": ""}]


def test_boolean_exit_is_read_as_a_number() -> None:
    config = Schema({"version": 1, "tests": [{"exit": True}, {"exit": False}]})
    assert [test["exit"] for test in config["tests"]] == [1, 0]


def test_min_points_must_be_positive() -> None:
    with pytest.raises(ValidationError):
        Schema({"version": 1, "min-points": 0, "tests": []})


def test_errors_point_to_the_right_model() -> None:
    with pytest.raises(ValidationError) as info:
        Schema({"version": 1, "tests": [{"tests": [{"stdout": [{"bogus": 1}]}]}]})
    first, hint = _humanize_errors(info.value).splitlines()
    assert first == "tests.0.tests.0.stdout.0.bogus: Extra inputs are not permitted"
    assert "newer Baygon" in hint


def test_invalid_test_fails_alone(tmp_path: Path) -> None:
    suite = build_suite_model(
        Schema(
            {
                "version": 1,
                "executable": sys.executable,
                "tests": [
                    {"name": "bad exit", "args": ["-c", ""], "exit": "zero"},
                    {
                        "name": "bad regex",
                        "args": ["-c", ""],
                        "stdout": [{"regex": "("}],
                    },
                    {"name": "fine", "args": ["-c", ""], "exit": 0},
                ],
            }
        )
    )
    report = BaygonRunner(suite, base_dir=tmp_path).run()
    bad_exit, bad_regex, fine = report.cases
    assert isinstance(bad_exit.issues[0], InvalidTestDefinition)
    assert "exit must be an integer, got 'zero'" in str(bad_exit.issues[0])
    assert isinstance(bad_regex.issues[0], InvalidTestDefinition)
    assert fine.status == "passed"


def test_points_sums_have_no_float_noise() -> None:
    assert _round_points(0.1 + 0.2) == 0.3
    assert _round_points(2.0) == 2


def test_report_with_yml_suffix_is_yaml(tmp_path: Path) -> None:
    cfg = tmp_path / "t.yml"
    cfg.write_text(f"version: 1\nexecutable: {sys.executable}\ntests:\n  - exit: 0\n")
    report = tmp_path / "report.yml"
    result = CliRunner().invoke(app, [f"--config={cfg}", f"--report={report}"])
    assert result.exit_code == 0, result.output
    assert yaml.safe_load(report.read_text())["successes"] == 1
    assert not report.read_text().lstrip().startswith("{")
