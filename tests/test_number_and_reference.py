"""Number/length/lines matchers, generated stdin and reference programs."""

from __future__ import annotations

from pathlib import Path
import sys

from pydantic import ValidationError
import pytest
from rich.console import Console

from baygon.core.models import build_suite_model
from baygon.filters import Filters
from baygon.matchers import (
    HelperProgramFailed,
    InvalidCount,
    InvalidNumber,
    InvalidSameAs,
    InvalidTestDefinition,
    MatchLength,
    MatchLines,
    MatchNumber,
)
from baygon.presentation import rich as rich_presentation
from baygon.runtime.runner import BaygonRunner
from baygon.schema import Schema

# --- Matchers ---------------------------------------------------------------


@pytest.mark.parametrize(
    ("spec", "output", "ok"),
    [
        ({"value": 12}, "12\n", True),
        ({"value": 12}, "12.0", True),
        ({"value": 12}, "12.1", False),
        ({"value": 0.1}, str(0.1 + 0.2 - 0.2), True),
        ({"value": 3.14, "tolerance": 0.01}, "3.1416", True),
        ({"value": 3.14, "tolerance": 0.001}, "3.1416", False),
        ({"min": 0, "max": 10}, "10", True),
        ({"min": 0, "max": 10}, "-0.5", False),
        ({"min": 5}, "1e3", True),
        ({"max": 5}, "nan", False),
        ({"value": 1}, "one", False),
        ({"value": "{{x}}"}, "1", None),  # not evaluated: invalid value
    ],
)
def test_number_matcher(spec, output, ok) -> None:
    if ok is None:
        with pytest.raises(ValueError, match="value must be a number"):
            MatchNumber(spec)
        return
    issue = MatchNumber(spec)(output, on="stdout")
    assert (issue is None) is ok
    negated = MatchNumber(spec, inverse=True)(output, on="stdout")
    assert (negated is None) is not ok


def test_number_messages() -> None:
    assert str(MatchNumber({"value": 2})("3", on="stdout")) == (
        "Output stdout is 3, expected 2."
    )
    assert str(MatchNumber({"value": 2, "tolerance": 0.5})("x", on="stdout")) == (
        'Output stdout is not a number: "x" (expected 2 ± 0.5).'
    )
    assert str(MatchNumber({"max": 1.5})("2", on="stdout")) == (
        "Output stdout is 2, expected at most 1.5."
    )
    assert str(MatchNumber({"min": 1, "max": 2}, inverse=True)("1", on="stdout")) == (
        "Output stdout is 1, it should not be between 1 and 2."
    )
    long_output = "x" * 100
    assert "..." in str(MatchNumber({"value": 1})(long_output, on="stdout"))
    assert isinstance(MatchNumber({"value": 1})("2"), InvalidNumber)


def test_length_and_lines_matchers() -> None:
    assert MatchLength({"value": 5})("hello") is None
    assert MatchLength({"min": 6})("hello") is not None
    assert MatchLines({"value": 0})("") is None
    assert MatchLines({"max": 2})("a\nb\n") is None
    issue = MatchLines({"min": 2, "max": 3})("a", on="stdout")
    assert isinstance(issue, InvalidCount)
    assert str(issue) == "Output stdout has 1 lines, expected between 2 and 3."
    negated = MatchLength({"value": 2}, inverse=True)("ab", on="stderr")
    assert str(negated) == (
        "Output stderr has 2 characters, it should not have exactly 2."
    )


# --- Schema -----------------------------------------------------------------


def _schema(condition):
    return Schema({"version": 1, "tests": [{"stdout": [condition]}]})


def test_schema_shorthands() -> None:
    stdout = _schema({"number": 1.5})["tests"][0]["stdout"][0]
    assert stdout["number"] == {"value": 1.5}
    stdout = _schema({"lines": 3, "length": {"min": 1.0}})["tests"][0]["stdout"][0]
    assert stdout["lines"] == {"value": 3}
    assert stdout["length"] == {"min": 1}
    negated = _schema({"not": [{"lines": {"max": 2}}]})["tests"][0]["stdout"][0]
    assert negated["not"] == [{"lines": {"max": 2}}]
    assert _schema({"same-as": "./ref"})["tests"][0]["stdout"][0]["same-as"] == "./ref"


@pytest.mark.parametrize(
    "condition",
    [
        {"number": {}},
        {"number": True},
        {"number": {"value": 1, "min": 0}},
        {"number": {"min": 3, "max": 1}},
        {"number": {"min": 0, "tolerance": 1}},
        {"number": {"value": 1, "tolerance": -1}},
        {"lines": 1.5},
        {"length": -1},
        {"not": [{"number": 1, "lines": 1}]},
    ],
)
def test_schema_rejects_invalid_specs(condition) -> None:
    with pytest.raises(ValidationError):
        _schema(condition)


def test_schema_stdin_command() -> None:
    config = Schema(
        {"version": 1, "tests": [{"stdin": {"executable": "./gen", "args": [1]}}]}
    )
    assert config["tests"][0]["stdin"] == {"executable": "./gen", "args": ["1"]}
    model = build_suite_model(config).tests[0]
    assert model.stdin is None
    assert model.stdin_command.executable == "./gen"
    assert model.stdin_command.args == ("1",)
    with pytest.raises(ValidationError):
        Schema({"version": 1, "tests": [{"stdin": {"args": []}}]})
    with pytest.raises(ValidationError):
        Schema({"version": 1, "tests": [{"stdin": {"executable": "x", "args": "a"}}]})


def test_filters_given_as_tuples() -> None:
    assert Filters({"replace": ("a", "x"), "regex": ("[0-9]", "")})("a1b2") == "xb"


# --- Runner with real programs ----------------------------------------------


def _script(tmp_path: Path, name: str, code: str) -> str:
    path = tmp_path / name
    path.write_text(f"#!{sys.executable}\n{code}\n", encoding="utf-8")
    path.chmod(0o755)
    return f"./{name}"


@pytest.fixture
def programs(tmp_path: Path) -> Path:
    _script(
        tmp_path,
        "gen.py",
        "import random, sys\n"
        "random.seed(int(sys.argv[1]))\n"
        "print(' '.join(str(random.randint(-50, 50)) for _ in range(6)))",
    )
    _script(tmp_path, "ref.py", "print(' '.join(sorted(input().split(), key=int)))")
    _script(tmp_path, "bad.py", "print(' '.join(sorted(input().split())))")
    _script(tmp_path, "fail.py", "import sys; sys.exit(3)")
    _script(tmp_path, "hang.py", "import time; time.sleep(60)")
    _script(tmp_path, "args.py", "import sys; print(*sys.argv[1:])")
    return tmp_path


def _run(tmp_path: Path, data: dict, **kwargs):
    suite = build_suite_model(Schema({"version": 1, **data}))
    return BaygonRunner(suite, base_dir=tmp_path, **kwargs).run()


def test_generated_stdin_and_reference(programs: Path) -> None:
    report = _run(
        programs,
        {
            "eval": True,
            "tests": [
                {
                    "name": "good",
                    "executable": "./ref.py",
                    "repeat": 3,
                    "stdin": {"executable": "./gen.py", "args": ["{{ iter() }}"]},
                    "stdout": [{"same-as": "./ref.py"}, {"lines": 1}],
                },
                {
                    "name": "bad",
                    "executable": "./bad.py",
                    "stdin": {"executable": "./gen.py", "args": [1]},
                    "stdout": [{"same-as": "./ref.py"}],
                },
            ],
        },
    )
    good, bad = report.cases
    assert good.status == "passed"
    roles = [command.role for command in good.commands]
    assert roles == ["generator", None, "reference"] * 3
    seeds = [command.argv[-1] for command in good.commands[::3]]
    assert seeds == ["0", "1", "2"]
    assert bad.status == "failed"
    assert isinstance(bad.issues[0], InvalidSameAs)
    assert "differs from the reference ./ref.py" in str(bad.issues[0])


def test_reference_gets_the_same_arguments(programs: Path) -> None:
    report = _run(
        programs,
        {
            "eval": True,
            "executable": "./args.py",
            "tests": [
                {
                    "args": ["{{ randint(0, 10**9) }}"],
                    "stdout": [{"same-as": "./args.py"}],
                    "stderr": [{"same-as": "./args.py"}],
                }
            ],
        },
    )
    (case,) = report.cases
    assert case.status == "passed"
    # stdout and stderr share one reference run
    assert [command.role for command in case.commands] == [None, "reference"]


def test_reference_filters_apply_to_both_outputs(programs: Path) -> None:
    report = _run(
        programs,
        {
            "executable": "./args.py",
            "tests": [
                {
                    "args": ["Hello"],
                    "stdout": [
                        {"filters": {"lowercase": True}, "same-as": "./args.py"}
                    ],
                }
            ],
        },
    )
    assert report.successes == 1


@pytest.mark.parametrize(
    ("data", "message"),
    [
        (
            {"stdin": {"executable": "./fail.py"}},
            "Generator ./fail.py failed: exit status 3.",
        ),
        ({"stdin": {"executable": "./missing.py"}}, "Generator ./missing.py failed:"),
        (
            {"stdin": {"executable": "./hang.py"}},
            "Generator ./hang.py failed: timeout after 0.3 s.",
        ),
        (
            {"stdout": [{"same-as": "./hang.py"}]},
            "Reference ./hang.py failed: timeout after 0.3 s.",
        ),
    ],
)
def test_helper_failures_fail_only_their_test(programs: Path, data, message) -> None:
    report = _run(
        programs,
        {
            "executable": "./args.py",
            "timeout": 0.3,
            "tests": [{"name": "helper", **data}, {"name": "fine", "args": ["x"]}],
        },
    )
    helper, fine = report.cases
    assert isinstance(helper.issues[0], HelperProgramFailed)
    assert str(helper.issues[0]).startswith(message)
    assert fine.status == "passed"


def test_reference_failing_with_a_status_is_fine(programs: Path) -> None:
    report = _run(
        programs,
        {"executable": "./fail.py", "tests": [{"stdout": [{"same-as": "./fail.py"}]}]},
    )
    assert report.successes == 1


def test_number_with_eval_and_filters(programs: Path) -> None:
    report = _run(
        programs,
        {
            "eval": True,
            "executable": "./args.py",
            "tests": [
                {
                    "args": ["Result:", "{{ x = 2 * pi }}"],
                    "stdout": [
                        {
                            "filters": {"regex": ["^Result: ", ""]},
                            "number": {"value": "{{ x }}", "tolerance": 1e-6},
                        },
                        {"not": [{"number": 0}]},
                    ],
                },
                {"args": ["1"], "stdout": [{"number": "{{ undefined_name }}"}]},
            ],
        },
    )
    good, bad = report.cases
    assert good.status == "passed", [str(i) for i in good.issues]
    assert isinstance(bad.issues[0], InvalidTestDefinition)


def test_command_panel_shows_the_role() -> None:
    from baygon.runtime.runner import CommandLog

    command = CommandLog(
        argv=("gen",), stdin=None, stdout="", stderr="", exit_status=0, role="generator"
    )
    console = Console(record=True, width=80)
    console.print(rich_presentation._command_panels((command,), hide_empty=True)[0])
    assert "Command #1 (generator)" in console.export_text()


def test_bare_executable_names_are_looked_up_in_path(tmp_path: Path) -> None:
    source = tmp_path / "main.c"
    source.write_text("int main(void) {\n    return 0;\n}\n", encoding="utf-8")
    report = _run(
        tmp_path,
        {
            "tests": [
                {
                    "executable": "grep",
                    "args": ["-c", "return", str(source)],
                    "stdout": [{"number": 1}],
                },
                {
                    "executable": "wc",
                    "args": ["-l", str(source)],
                    "stdout": [
                        {
                            "filters": {"regex": [r"\s*(\d+).*", r"\1"]},
                            "number": {"max": 3},
                        }
                    ],
                },
            ]
        },
    )
    assert [case.status for case in report.cases] == ["passed", "passed"], [
        str(issue) for case in report.cases for issue in case.issues
    ]


def test_file_next_to_the_config_wins_over_path(tmp_path: Path) -> None:
    _script(tmp_path, "grep", "print('local')")
    report = _run(tmp_path, {"tests": [{"executable": "grep", "stdout": "local\n"}]})
    assert report.successes == 1


def test_forbidden_programs_stay_forbidden(tmp_path: Path) -> None:
    from baygon.error import InvalidExecutableError

    with pytest.raises(InvalidExecutableError, match="forbidden"):
        _run(tmp_path, {"tests": [{"executable": "rm", "args": ["-rf", "x"]}]})


def test_filters_on_tests_and_groups(tmp_path: Path) -> None:
    report = _run(
        tmp_path,
        {
            "executable": "echo",
            "filters": {"trim": True},
            "tests": [
                {"args": ["Hello"], "filters": {"lowercase": True}, "stdout": "hello"},
                {
                    "filters": {"uppercase": True},
                    "tests": [{"args": ["Hi"], "stdout": "HI"}],
                },
                {"args": ["Hello"], "stdout": "Hello"},
            ],
        },
    )
    assert report.successes == 3, [str(i) for c in report.cases for i in c.issues]
