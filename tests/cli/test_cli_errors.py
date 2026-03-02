from __future__ import annotations

from pathlib import Path
import runpy
import sys
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from baygon.__main__ import app


def test_cli_reports_loader_error(tmp_path: Path) -> None:
    bad_config = tmp_path / "bad.txt"
    bad_config.write_text("tests: []", encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(app, [f"--config={bad_config}"])

    assert result.exit_code == 1
    assert "Unknown file extension" in result.output


def test_cli_prevents_executable_override(tmp_path: Path) -> None:
    cfg = tmp_path / "with_exec.yml"
    cfg.write_text(
        "\n".join(
            [
                "version: 1",
                f"executable: {sys.executable}",
                "tests:",
                "  - exit: 0",
            ]
        ),
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(app, [f"--config={cfg}", sys.executable])

    assert result.exit_code == 1
    assert "Executable can't be overridden" in result.output


def test_main_run_invokes_app() -> None:
    from baygon import __main__ as main

    with patch.object(main, "app") as mock_app:
        mock_app.return_value = None
        main.run()

    mock_app.assert_called_once()


def test_module_entrypoint(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["baygon", "--version"], raising=False)

    with pytest.raises(SystemExit):
        runpy.run_module("baygon.__main__", run_name="__main__")
