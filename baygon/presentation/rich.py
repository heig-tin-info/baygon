"""Rich presentation utilities for Baygon."""

from __future__ import annotations

from collections.abc import Sequence

from rich.box import SQUARE_DOUBLE_HEAD
from rich.console import Console, Group
from rich.panel import Panel
from rich.rule import Rule
from rich.style import Style
from rich.table import Table
from rich.text import Text

from baygon.helpers import create_command_line
from baygon.runtime.runner import CaseResult, CommandLog, RunReport


def render_summary_table(report: RunReport, *, console: Console) -> None:
    """Render a summary table for the given report."""
    grey_line_style = Style(color="grey37")
    title_style = Style(bold=False, color="white")
    table = Table(
        title="Test Summary",
        title_style=title_style,
        border_style=grey_line_style,
        box=SQUARE_DOUBLE_HEAD,
    )

    table.add_column("ID", justify="left")
    table.add_column("Test Name", justify="left", style=grey_line_style)
    table.add_column("Points", justify="center", style=grey_line_style)
    table.add_column("Status", justify="center", style=grey_line_style)

    for result in report.cases:
        status = _format_status(result.status)
        points_value = ""
        if result.points_earned is not None and result.case.points is not None:
            points_value = f"{result.points_earned}/{result.case.points}"
        table.add_row(
            result.case.id_str,
            f"{result.case.name}",
            points_value,
            status,
        )

    console.print(table)


def render_pretty_failures(report: RunReport, *, console: Console) -> None:
    """Render rich failure panels for failing cases."""
    for result in report.cases:
        if result.status != "failed":
            continue
        console.print(_build_pretty_failure_panel(result))


def render_command_panels(
    result: CaseResult,
    *,
    console: Console,
    hide_empty_streams: bool,
) -> None:
    """Render command telemetry panels for a case."""
    panels = _command_panels(result.commands, hide_empty=hide_empty_streams)
    for panel in panels:
        console.print(panel)


def _format_status(status: str | bool) -> str:
    if isinstance(status, bool):
        status = "passed" if status else "failed"
    normalized = str(status).lower()
    if normalized in {"passed", "true"}:
        return "[green]PASS[/green]"
    if normalized in {"failed", "false"}:
        return "[red]FAIL[/red]"
    if normalized == "skipped":
        return "[yellow]SKIPPED[/yellow]"
    return str(status)


def _build_pretty_failure_panel(result: CaseResult) -> Panel:
    summary = Table.grid(padding=(0, 1))
    summary.add_column(style="grey50", justify="right")
    summary.add_column()
    summary.add_row("path", result.case.name)
    summary.add_row("status", Text("FAILED", style="bold red"))
    summary.add_row("points", f"0/{result.case.points or 0}")

    issues_table = Table.grid(padding=(0, 1))
    issues_table.add_column(style="red bold", justify="right")
    issues_table.add_column()
    if not result.issues:
        issues_table.add_row("", Text("No matcher issues recorded.", style="dim"))
    else:
        for index, issue in enumerate(result.issues, start=1):
            issues_table.add_row(
                f"#{index}",
                Text(str(issue), style="white", overflow="fold"),
            )
    issues_panel = Panel(issues_table, title="issues", border_style="red")

    renderables = [summary, Rule(style="grey37"), issues_panel]

    command_panels = _command_panels(result.commands, hide_empty=True)
    if command_panels:
        renderables.extend([Rule(style="grey37"), Group(*command_panels)])
    else:
        renderables.extend(
            [
                Rule(style="grey37"),
                Text("No command telemetry captured.", style="dim"),
            ]
        )

    return Panel(
        Group(*renderables),
        title=f"Test {result.case.id_str}: {result.case.name}",
        border_style="red",
    )


def _command_panels(
    commands: Sequence[CommandLog],
    *,
    hide_empty: bool,
) -> list[Panel]:
    return [
        _build_command_panel(command, index, hide_empty=hide_empty)
        for index, command in enumerate(commands, start=1)
    ]


def _build_command_panel(
    command: CommandLog,
    index: int,
    *,
    hide_empty: bool,
) -> Panel:
    meta_table = Table.grid(padding=(0, 1))
    meta_table.add_column(style="cyan bold", justify="right")
    meta_table.add_column()
    meta_table.add_row("command", create_command_line(command.argv))
    meta_table.add_row("exit", str(command.exit_status))

    args_panel = _build_stream_panel(
        title="args",
        value=command.argv[1:],
        placeholder="<none>",
        style="white",
        border_style="cyan",
        hide_empty=hide_empty,
    )
    stdin_panel = _build_stream_panel(
        title="stdin",
        value=command.stdin,
        placeholder="<empty>",
        style="white",
        border_style="yellow",
        hide_empty=hide_empty,
        empty_border_style="grey37",
    )
    stdout_panel = _build_stream_panel(
        title="stdout",
        value=command.stdout,
        placeholder="<empty>",
        style="green",
        border_style="green",
        hide_empty=hide_empty,
    )
    stderr_panel = _build_stream_panel(
        title="stderr",
        value=command.stderr,
        placeholder="<empty>",
        style="red",
        border_style="red",
        hide_empty=hide_empty,
        empty_border_style="grey37",
    )

    stream_panels = [
        panel
        for panel in (args_panel, stdin_panel, stdout_panel, stderr_panel)
        if panel is not None
    ]

    renderables = [meta_table]
    if stream_panels:
        renderables.append(Rule(style="grey37"))
        renderables.append(Group(*stream_panels))

    return Panel(Group(*renderables), title=f"Command #{index}", border_style="cyan")


def _build_stream_panel(
    *,
    title: str,
    value,
    placeholder: str,
    style: str,
    border_style: str,
    hide_empty: bool,
    empty_border_style: str | None = None,
) -> Panel | None:
    text_value = _normalize_stream_value(value)
    is_empty = text_value == "" or text_value is None

    if hide_empty and is_empty:
        return None

    display_text = placeholder if is_empty else text_value
    applied_style = style if not is_empty else "dim"
    applied_border = border_style
    if empty_border_style is not None and is_empty:
        applied_border = empty_border_style

    return Panel(
        Text(display_text, style=applied_style, overflow="fold", no_wrap=False),
        title=title,
        border_style=applied_border,
    )


def _normalize_stream_value(value) -> str | None:
    if value is None:
        return None
    if isinstance(value, (bytes, bytearray)):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, (list, tuple)):
        return " ".join(str(item) for item in value)
    return str(value)
