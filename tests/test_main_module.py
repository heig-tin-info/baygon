"""Unit tests targeting helpers in baygon.__main__."""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest
import typer
import yaml

from baygon.__main__ import (
    Runner,
    _format_callback,
    _version_callback,
    console,
    display_pad,
    display_table,
    display_test_name,
    save_report,
)


class DummyId:
    def __init__(self, value: str) -> None:
        self.value = value

    def pad(self) -> str:
        return f"{self.value} "

    def __str__(self) -> str:
        return self.value


class DummyTest:
    def __init__(self, value: str) -> None:
        self.id = DummyId(value)
        self.name = f"Test {value}"
        self.points = 1


def _build_runner(pretty: bool) -> Runner:
    runner = Runner.__new__(Runner)  # type: ignore[call-arg]
    runner.pretty = pretty
    runner.ran_commands = []
    return runner


def test_display_pad_outputs_spacing(capsys: pytest.CaptureFixture[str]) -> None:
    display_pad()
    display_pad(3)
    out = capsys.readouterr().out
    assert "  " in out
    assert "..." in out


def test_display_test_name_formats_output(capsys: pytest.CaptureFixture[str]) -> None:
    display_test_name(DummyTest("1.1"))
    out = capsys.readouterr().out
    assert "Test 1.1" in out
    assert "Test 1.1: Test 1.1" in out


def test_display_table_renders_statuses() -> None:
    payload = [
        {"id": "1", "name": "Pass Case", "status": "passed", "points": 1, "earned": 1},
        {"id": "2", "name": "Fail Case", "status": False, "points": 2, "earned": 0},
        {"id": "3", "name": "Skip Case", "status": "skipped"},
        {"id": "4", "name": "Custom Case", "status": "unknown"},
    ]
    with console.capture() as capture:
        display_table(payload)
    output = capture.get()
    assert "PASS" in output
    assert "FAIL" in output
    assert "SKIPPED" in output
    assert "unknown" in output


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


def test_save_report_json_and_yaml(tmp_path) -> None:
    data = {"alpha": 1, "beta": {"gamma": 2}}

    json_path = tmp_path / "report.json"
    save_report(data, str(json_path), "json")
    assert json.loads(json_path.read_text())["beta"]["gamma"] == 2

    yaml_path = tmp_path / "report.yaml"
    save_report(data, str(yaml_path), "yaml")
    assert yaml.safe_load(yaml_path.read_text())["alpha"] == 1


def test_pretty_stream_panel_omits_empty_values() -> None:
    runner = _build_runner(pretty=True)
    panel = runner._build_stream_panel(
        title="stdout",
        value="",
        placeholder="<empty>",
        style="green",
        border_style="green",
    )
    assert panel is None


def test_non_pretty_stream_panel_renders_placeholder() -> None:
    runner = _build_runner(pretty=False)
    panel = runner._build_stream_panel(
        title="stdout",
        value="",
        placeholder="<empty>",
        style="green",
        border_style="green",
    )
    assert panel is not None
    renderable = getattr(panel, "renderable", None)
    assert renderable is not None
    plain_text = getattr(renderable, "plain", str(renderable))
    assert "<empty>" in plain_text


def test_render_pretty_failure_without_commands() -> None:
    runner = _build_runner(pretty=True)
    dummy_test = SimpleNamespace(id="1.1", name="Nested Case", points=1)
    with console.capture() as capture:
        runner._render_pretty_failure(dummy_test, [], "Group / Nested Case")
    output = capture.get()
    assert "No matcher issues recorded." in output
    assert "No command telemetry captured." in output
