"""CLI options: test selection, timeout, strict mode and detailed reports."""

from __future__ import annotations

import json
from pathlib import Path
import sys

from typer.testing import CliRunner

from baygon.__main__ import app


def _config(tmp_path: Path, body: str) -> Path:
    cfg = tmp_path / "t.yml"
    cfg.write_text(f"version: 1\nexecutable: {sys.executable}\n{body}", "utf-8")
    return cfg


SUITE = """\
tests:
  - name: Passes
    args: [-c, "print(1)"]
    stdout: "1\\n"
  - name: Group
    tests:
      - name: Fails
        args: [-c, "print(2)"]
        stdout: "1\\n"
      - name: Hangs
        args: [-c, "import time; time.sleep(60)"]
"""


def _invoke(*args: str):
    return CliRunner().invoke(app, list(args))


def test_failures_exit_zero_by_default(tmp_path: Path) -> None:
    cfg = _config(tmp_path, SUITE)
    result = _invoke(f"--config={cfg}", "--only", "2.1")
    assert result.exit_code == 0
    assert "Test 2.1: Fails FAILED" in result.output
    assert "Test 1:" not in result.output


def test_strict_exits_one_on_failure(tmp_path: Path) -> None:
    cfg = _config(tmp_path, SUITE)
    assert _invoke(f"--config={cfg}", "--only", "2.1", "--strict").exit_code == 1
    assert _invoke(f"--config={cfg}", "--only", "1", "--strict").exit_code == 0


def test_cli_timeout_and_detailed_report(tmp_path: Path) -> None:
    cfg = _config(tmp_path, SUITE)
    report = tmp_path / "report.json"
    result = _invoke(f"--config={cfg}", "--timeout", "0.3", f"--report={report}")
    assert result.exit_code == 0, result.output
    assert "Timeout after 0.3 s." in result.output

    data = json.loads(report.read_text("utf-8"))
    assert data["total"] == 3
    assert [case["status"] for case in data["cases"]] == ["passed", "failed", "failed"]
    assert data["groups"][0]["id"] == "2"
    assert data["groups"][0]["failures"] == 2


def test_keyword_and_comma_separated_ids(tmp_path: Path) -> None:
    cfg = _config(tmp_path, SUITE)
    result = _invoke(f"--config={cfg}", "-k", "pass")
    assert "Test 1: Passes PASSED" in result.output
    assert "Ran 1 tests" in result.output

    result = _invoke(f"--config={cfg}", "--only", "1,2.1")
    assert "Ran 2 tests" in result.output


def test_empty_selection_is_an_error(tmp_path: Path) -> None:
    cfg = _config(tmp_path, SUITE)
    result = _invoke(f"--config={cfg}", "--only", "7")
    assert result.exit_code == 1
    assert "no test selected" in result.output


def test_invalid_id_is_an_error(tmp_path: Path) -> None:
    cfg = _config(tmp_path, SUITE)
    result = _invoke(f"--config={cfg}", "--only", "x")
    assert result.exit_code == 1
    assert "Invalid test id" in result.output


def test_invalid_timeout_option(tmp_path: Path) -> None:
    cfg = _config(tmp_path, SUITE)
    result = _invoke(f"--config={cfg}", "--timeout", "0")
    assert result.exit_code == 2


def test_invalid_configuration_is_readable(tmp_path: Path) -> None:
    cfg = _config(tmp_path, "timeout: -1\nunknown: 1\ntests: []\n")
    result = _invoke(f"--config={cfg}")
    assert result.exit_code == 1
    assert "invalid configuration" in result.output
    assert "timeout: Value error, timeout must be greater than 0" in result.output
    assert "unknown: Extra inputs are not permitted" in result.output
    assert "Traceback" not in result.output
