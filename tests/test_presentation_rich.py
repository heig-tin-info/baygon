from __future__ import annotations

from rich.console import Console

from baygon.core.models import CaseModel
from baygon.presentation import rich as rich_presentation
from baygon.runtime.runner import CaseResult, CommandLog


def _make_case(name: str) -> CaseModel:
    return CaseModel(
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


def test_format_status_variants() -> None:
    assert "PASS" in rich_presentation._format_status(True)
    assert "FAIL" in rich_presentation._format_status(False)
    assert "SKIPPED" in rich_presentation._format_status("skipped")
    assert "custom" in rich_presentation._format_status("custom")


def test_build_pretty_failure_panel_handles_empty() -> None:
    case = _make_case("sample")
    result = CaseResult(case=case, status="failed", issues=(), commands=())
    console = Console(record=True)
    console.print(rich_presentation._build_pretty_failure_panel(result))
    assert "No matcher issues" in console.export_text()


def test_command_panels_with_bytes_streams() -> None:
    command = CommandLog(
        argv=("/bin/echo", "arg"),
        stdin=b"data",
        stdout="output",
        stderr="",
        exit_status=0,
    )
    panels = rich_presentation._command_panels((command,), hide_empty=False)
    assert len(panels) == 1
    assert "Command #1" in panels[0].title
    assert rich_presentation._normalize_stream_value(b"bin") == "bin"
