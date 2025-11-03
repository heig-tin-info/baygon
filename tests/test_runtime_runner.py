from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import pytest

from baygon.core.models import build_suite_model
from baygon.error import InvalidExecutableError
from baygon.executable import Outputs
from baygon.runtime.runner import BaygonRunner
from baygon.schema import Schema


@dataclass
class FakeExecutable:
    path: str
    responses: dict[tuple[str, ...], tuple[int, str, str]]

    def run(
        self,
        *args: str,
        stdin: str | None = None,
        env: dict[str, Any] | None = None,
        hook: Callable[..., None] | None = None,
    ) -> Outputs:
        response = self.responses.get(tuple(args))
        if response is None:
            raise AssertionError(f"Unexpected command arguments: {args!r}")
        exit_status, stdout, stderr = response
        if hook:
            hook(
                cmd=[self.path, *args],
                stdin=stdin,
                stdout=stdout,
                stderr=stderr,
                exit_status=exit_status,
            )
        return Outputs(exit_status=exit_status, stdout=stdout, stderr=stderr)


def _suite_from_dict(data: dict[str, Any]):
    config = Schema(data)
    return build_suite_model(config)


def _fake_factory(responses: dict[tuple[str, ...], tuple[int, str, str]]):
    def _factory(path: str) -> FakeExecutable:
        return FakeExecutable(path=path, responses=responses)

    return _factory


def test_runner_passes_case(tmp_path: Path) -> None:
    suite = _suite_from_dict(
        {
            "version": 1,
            "tests": [
                {
                    "name": "Echo",
                    "args": ["42"],
                    "stdout": [{"equals": "42"}],
                }
            ],
        }
    )
    runner = BaygonRunner(
        suite,
        base_dir=tmp_path,
        executable="prog",
        executable_factory=_fake_factory({("42",): (0, "42", "")}),
    )
    report = runner.run()

    assert report.failures == 0
    assert report.successes == 1
    result = report.cases[0]
    assert result.status == "passed"
    assert result.commands[0].argv[-1] == "42"


def test_runner_reports_failure(tmp_path: Path) -> None:
    suite = _suite_from_dict(
        {
            "version": 1,
            "tests": [
                {
                    "name": "Mismatch",
                    "args": ["info"],
                    "stdout": [{"equals": "expected"}],
                }
            ],
        }
    )
    runner = BaygonRunner(
        suite,
        base_dir=tmp_path,
        executable="prog",
        executable_factory=_fake_factory({("info",): (0, "actual", "")}),
    )
    report = runner.run()
    result = report.cases[0]

    assert report.failures == 1
    assert result.status == "failed"
    assert result.issues, "Expected at least one issue for mismatch"


def test_runner_respects_failure_limit(tmp_path: Path) -> None:
    suite = _suite_from_dict(
        {
            "version": 1,
            "tests": [
                {
                    "name": "First",
                    "args": ["one"],
                    "stdout": [{"equals": "ok"}],
                },
                {
                    "name": "Second",
                    "args": ["two"],
                    "stdout": [{"equals": "ok"}],
                },
                {
                    "name": "Third",
                    "args": ["three"],
                    "stdout": [{"equals": "ok"}],
                },
            ],
        }
    )
    responses = {
        ("one",): (1, "ko", ""),
        ("two",): (1, "ko", ""),
        ("three",): (1, "ko", ""),
    }
    runner = BaygonRunner(
        suite,
        base_dir=tmp_path,
        executable="prog",
        executable_factory=_fake_factory(responses),
    )
    report = runner.run(limit=1)

    assert report.failures == 2
    assert len(report.cases) == 2


def test_cli_executable_cannot_override_config(tmp_path: Path) -> None:
    suite = _suite_from_dict(
        {
            "version": 1,
            "executable": "config-bin",
            "tests": [{"name": "Sample", "args": [], "stdout": []}],
        }
    )
    with pytest.raises(InvalidExecutableError):
        BaygonRunner(
            suite,
            base_dir=tmp_path,
            executable="cli-bin",
        )


def test_case_cannot_override_parent_executable(tmp_path: Path) -> None:
    suite = _suite_from_dict(
        {
            "version": 1,
            "executable": "root-bin",
            "tests": [
                {
                    "name": "Invalid",
                    "executable": "other",
                    "stdout": [],
                }
            ],
        }
    )
    runner = BaygonRunner(
        suite,
        base_dir=tmp_path,
    )
    with pytest.raises(InvalidExecutableError):
        runner.run()
