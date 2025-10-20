"""Main CLI command."""

from __future__ import annotations

import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import typer
from rich.box import SQUARE_DOUBLE_HEAD
from rich.console import Console, Group
from rich.panel import Panel
from rich.rule import Rule
from rich.style import Style
from rich.table import Table
from rich.text import Text
from typer import BadParameter

from . import TestCase, TestGroup, TestSuite, __copyright__, __version__
from .error import InvalidExecutableError
from .helpers import create_command_line

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("baygon")

console = Console()
app = typer.Typer(
    help="Baygon functional test runner.",
    context_settings={"allow_interspersed_args": True},
)


def display_pad(pad: int = 0) -> None:
    """Display a pad of spaces to align nested output."""
    typer.secho("." * pad if pad > 0 else "  ", nl=False, dim=pad == 0)


def test_name_length(test):
    """Compute the length of test name."""
    return len(f"{test.id.pad()}Test {test.id}: {test.name}")


def display_test_name(test):
    """Display the name of a test."""
    typer.secho(f"{test.id.pad()}Test {test.id}: ", nl=False, bold=True)
    typer.secho(f"{test.name}", nl=False, bold=False)


def display_table(data):
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

    for test in data:
        status = ""
        points = ""
        status_value = test.get("status")
        if status_value is not None:
            normalized = status_value
            if isinstance(status_value, str):
                normalized = status_value.lower()

            if normalized in (True, "passed"):
                status = "[green]PASS[/green]"
            elif normalized in (False, "failed"):
                status = "[red]FAIL[/red]"
            elif normalized == "skipped":
                status = "[yellow]SKIPPED[/yellow]"
            else:
                status = str(status_value)

            if "earned" in test and "points" in test:
                points = f"{test['earned']}/{test['points']}"

        table.add_row(
            str(test["id"]), (" " * len(test["id"])) + test["name"], points, status
        )
    console.print(table)


class OneLineExceptionFormatter(logging.Formatter):
    """A formatter that displays the exception on a single line."""

    def format_exception(self, exc_info):
        """Format an exception."""
        result = super().format_exception(exc_info)
        return repr(result)

    def format(self, record):
        """Format a log record."""
        result = super().format(record)
        if record.exc_text:
            result = result.replace("\n", "")
        return result


class Runner:
    """Test runner."""

    def __init__(self, executable=None, config=None, **kwargs):
        self.executable = executable
        self.limit = kwargs.get("limit", -1)
        typer.secho(f"Using configuration file: {config}")
        self.test_suite = TestSuite(path=config, executable=self.executable)

        # Forward cli arguments to the test suite
        if "verbose" in kwargs and kwargs["verbose"] != 0:
            self.test_suite.config["verbose"] = kwargs["verbose"]
        if "report" in kwargs and kwargs["report"] is not None:
            self.test_suite.config["report"] = kwargs["report"]
        if "format" in kwargs and kwargs["format"] is not None:
            self.test_suite.config["format"] = kwargs["format"]
        if "table" in kwargs and kwargs["table"] is not None:
            self.test_suite.config["table"] = kwargs["table"]

        self.verbose = kwargs.get("verbose", 0)
        self.pretty = kwargs.get("pretty", False)
        if self.verbose > 0:
            typer.echo("Verbose level set to " + str(self.verbose))

        if self.verbose > 3:
            self._init_logger("DEBUG")

        self.align_column = 0

        self.failures = 0
        self.successes = 0
        self.skipped = 0
        self.run_time = 0

        self.points_earned = 0
        self.points_total = 0

        self.summary = []
        self.ran_commands: List[Dict[str, Any]] = []

    def _init_logger(self, loglevel):
        handler = logging.StreamHandler()
        formatter = OneLineExceptionFormatter(logging.BASIC_FORMAT)
        handler.setFormatter(formatter)
        root = logging.getLogger()
        root.setLevel(os.environ.get("LOGLEVEL", loglevel))
        root.addHandler(handler)

    def get_report(self):
        self.test_suite.get_points()
        return {
            "failures": self.failures,
            "successes": self.successes,
            "skipped": self.skipped,
            "total": self.failures + self.successes + self.skipped,
            "time": self.run_time,
            "points": {
                "total": self.points_total,
                "earned": self.points_earned,
            },
        }

    def run(self):
        """Run the tests."""
        start_time = time.time()
        self.align_column = self._max_length(self.test_suite) + 10

        self.failures = 0
        self.successes = 0
        self.skipped = 0
        self.points_total = 0
        self.points_earned = 0

        self._traverse_group(self.test_suite)

        if self.test_suite.config.get("table"):
            display_table(self.summary)

        tests = self.failures + self.successes + self.skipped
        seconds = round(time.time() - start_time, 2)
        self.run_time = seconds
        console.print(f"\nRan [bold]{tests}[/bold] tests in [bold]{seconds} s[/bold].")

        if self.points_total > 0:
            typer.secho(
                f"Points: {self.points_earned}/{self.points_total}",
                bold=True,
            )

        if self.failures > 0:
            ratio = 100 - round(
                self.failures / (self.failures + self.successes) * 100, 2
            )
            typer.secho(
                (f"{self.failures} failed, {self.successes} " f"passed ({ratio}% ok)."),
                fg="yellow",
                bold=True,
            )
            typer.secho("\nfail.", fg="red", bold=True)
        else:
            typer.secho("\nok.", fg="green")

        if self.skipped > 0:
            typer.secho(
                (
                    f"{self.skipped} test(s) skipped, "
                    "some executables may be missing."
                ),
                fg="yellow",
            )

        report = self.test_suite.config.get("report")
        report_format = self.test_suite.config.get("format")
        if report:
            if not report_format:
                if report.endswith(".yaml"):
                    report_format = "yaml"
                else:
                    report_format = "json"
            save_report(self.get_report(), report, report_format)

        return self.failures

    def _max_length(self, tests):
        length = 0
        for test in tests:
            length = max(test_name_length(test), length)
            if isinstance(test, TestGroup):
                length = max(self._max_length(test), length)
        return length

    def hook_ran_command(self, cmd, stdin, stdout, stderr, exit_status, **kwargs):
        """Capture executed command for logging purpose."""
        # If element have a space, wrap it with quotes

        cmdline = create_command_line(cmd)
        stdin_text = (
            stdin.decode("utf-8") if isinstance(stdin, (bytes, bytearray)) else ""
        )
        self.ran_commands.append(
            {
                "command": cmdline,
                "args": list(cmd[1:]),
                "stdin": stdin_text,
                "stdout": stdout,
                "stderr": stderr,
                "exit_status": exit_status,
            }
        )

    def pad(self, text, length):
        """Shift text to right
        >>> pad("hello", 5)"
        '     hello'
        >>> pad("hello\nworld", 3)"
        '   hello\n   world'
        """
        return "\n".join(" " * length + line for line in text.splitlines())

    def display_test_verbose(self, test, issues, verbose=0):  # noqa: C901
        p = test
        name_parts = []
        while True:
            if p is None or getattr(p, "name", None) is None:
                break
            if p.name:
                name_parts.append(p.name)
            p = p.parent
        breadcrumb = " / ".join(reversed(name_parts))

        pretty_failure = self.pretty and test.status == "failed"

        if verbose >= 2 and not pretty_failure:
            console.print("\n")
            console.print(
                Rule(
                    f"Test {test.id}: {breadcrumb}",
                    align="left",
                    style="bold",
                )
            )

        if verbose >= 3 and not pretty_failure:
            for panel in self._command_panels():
                console.print(panel)

        if test.status == "skipped":
            if verbose > 0:
                typer.secho(" SKIPPED", fg="yellow")
            else:
                typer.secho("S", fg="yellow", nl=False)
            self.skipped += 1
            return

        if test.status == "passed":
            if verbose > 0:
                typer.secho(" PASSED", fg="green")
            else:
                typer.secho(".", fg="green", nl=False)
            self.successes += 1
            return

        if test.status == "failed":
            if verbose > 0:
                typer.secho(" FAILED", fg="red")
            else:
                typer.secho("F", fg="red", nl=False)
                if pretty_failure:
                    typer.echo()
            self.failures += 1
            if pretty_failure:
                self._render_pretty_failure(test, issues, breadcrumb)
            else:
                for issue in issues:
                    typer.secho(str(issue))
            return

        for issue in issues:
            typer.secho(str(issue))

    def _normalize_stream_value(self, value: Any) -> Optional[str]:
        """Return a string representation for stream values."""
        if value is None:
            return None
        if isinstance(value, (bytes, bytearray)):
            if not value:
                return ""
            return value.decode("utf-8", errors="replace")
        if isinstance(value, (list, tuple)):
            return " ".join(str(item) for item in value)
        return str(value)

    def _build_stream_panel(
        self,
        *,
        title: str,
        value: Any,
        placeholder: str,
        style: str,
        border_style: str,
        empty_border_style: Optional[str] = None,
    ) -> Optional[Panel]:
        """Create a panel for a specific stream unless it is empty in pretty mode."""
        text_value = self._normalize_stream_value(value)
        is_empty = text_value is None or text_value == ""
        if self.pretty and is_empty:
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

    def _build_command_panel(self, command: Dict[str, Any], index: int) -> Panel:
        meta_table = Table.grid(padding=(0, 1))
        meta_table.add_column(style="cyan bold", justify="right")
        meta_table.add_column()
        meta_table.add_row("command", command.get("command", ""))
        meta_table.add_row("exit", str(command.get("exit_status")))

        args_panel = self._build_stream_panel(
            title="args",
            value=command.get("args"),
            placeholder="<none>",
            style="white",
            border_style="cyan",
        )
        stdin_panel = self._build_stream_panel(
            title="stdin",
            value=command.get("stdin"),
            placeholder="<empty>",
            style="white",
            border_style="yellow",
        )
        stdout_panel = self._build_stream_panel(
            title="stdout",
            value=command.get("stdout"),
            placeholder="<empty>",
            style="green",
            border_style="green",
        )
        stderr_panel = self._build_stream_panel(
            title="stderr",
            value=command.get("stderr"),
            placeholder="<empty>",
            style="red",
            border_style="red",
            empty_border_style="grey37",
        )

        stream_panels = [
            panel
            for panel in (args_panel, stdin_panel, stdout_panel, stderr_panel)
            if panel is not None
        ]
        renderables: List[Any] = [meta_table]
        if stream_panels:
            renderables.append(Rule(style="grey37"))
            renderables.append(Group(*stream_panels))

        return Panel(
            Group(*renderables),
            title=f"Command #{index}",
            border_style="cyan",
        )

    def _command_panels(self) -> List[Panel]:
        return [
            self._build_command_panel(command, index)
            for index, command in enumerate(self.ran_commands, start=1)
        ]

    def _render_pretty_failure(self, test, issues, breadcrumb: str) -> None:
        summary = Table.grid(padding=(0, 1))
        summary.add_column(style="grey50", justify="right")
        summary.add_column()
        summary.add_row("path", breadcrumb or test.name)
        summary.add_row("status", Text("FAILED", style="bold red"))
        summary.add_row("points", f"0/{test.points}")

        issues_table = Table.grid(padding=(0, 1))
        issues_table.add_column(style="red bold", justify="right")
        issues_table.add_column()
        if not issues:
            issues_table.add_row("", Text("No matcher issues recorded.", style="dim"))
        else:
            for index, issue in enumerate(issues, start=1):
                issues_table.add_row(
                    f"#{index}",
                    Text(str(issue), style="white", overflow="fold"),
                )
        issues_panel = Panel(issues_table, title="issues", border_style="red")

        renderables: List[Any] = [summary, Rule(style="grey37"), issues_panel]

        command_panels = self._command_panels()
        if command_panels:
            renderables.extend([Rule(style="grey37"), Group(*command_panels)])
        else:
            renderables.extend(
                [
                    Rule(style="grey37"),
                    Text("No command telemetry captured.", style="dim"),
                ]
            )

        console.print(
            Panel(
                Group(*renderables),
                title=f"Test {test.id}: {test.name}",
                border_style="red",
            )
        )

    def _run_test(self, test):
        self.ran_commands = []
        hook = self.hook_ran_command
        issues = test.run(hook)
        if issues is None:
            test.status = "skipped"
        elif not issues:
            test.status = "passed"
        else:
            test.status = "failed"

        self.display_test_verbose(test, issues, self.verbose)

        earned_points = test.points if test.status == "passed" else 0
        self.points_total += test.points
        self.points_earned += earned_points
        self.summary.append(
            {
                "id": test.id,
                "name": test.name,
                "status": test.status,
                "points": test.points,
                "earned": earned_points,
            }
        )

    def _traverse_group(self, tests):
        for test in tests:
            if self.limit > 0 and self.failures > self.limit:
                break

            if isinstance(test, TestGroup):
                self.summary.append(
                    {
                        "id": test.id,
                        "name": test.name,
                    }
                )
                self._traverse_group(test)
            elif isinstance(test, TestCase):
                self._run_test(test)
        return self.failures


def save_report(data, filename, format):
    """Save the report to a file."""
    if format == "json":
        import json

        with open(filename, "w") as fp:
            json.dump(data, fp, indent=2, sort_keys=True)
    elif format == "yaml":
        import yaml

        with open(filename, "w") as fp:
            yaml.dump(data, fp)


def version():
    """Display the version."""
    print(f"Baygon version {__version__} {__copyright__}")


def _version_callback(version_requested: bool) -> None:
    if version_requested:
        version()
        raise typer.Exit()


def _format_callback(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    normalized = value.lower()
    if normalized not in {"json", "yaml"}:
        raise BadParameter("Format must be 'json' or 'yaml'.")
    return normalized


@app.callback(invoke_without_command=True)
def cli(
    executable: Optional[Path] = typer.Argument(
        None,
        exists=True,
        dir_okay=False,
        readable=True,
        resolve_path=True,
        help="Path to the executable under test.",
    ),
    _version: bool = typer.Option(
        False,
        "--version",
        callback=_version_callback,
        is_eager=True,
        help="Show version information and exit.",
    ),
    verbose: int = typer.Option(
        0,
        "-v",
        "--verbose",
        count=True,
        help="Increase verbosity. Use -vvv for detailed command frames.",
    ),
    limit: int = typer.Option(-1, "-l", "--limit", help="Limit errors to N."),
    debug: bool = typer.Option(False, "-d", "--debug", help="Enable debug mode."),
    report: Optional[Path] = typer.Option(
        None,
        "-r",
        "--report",
        writable=True,
        resolve_path=True,
        help="Write report to the given file.",
    ),
    table: bool = typer.Option(
        False, "-T", "--table", help="Display a rich summary table."
    ),
    pretty: bool = typer.Option(
        False,
        "-p",
        "--pretty",
        help="Display nested frames for failing tests.",
    ),
    format: Optional[str] = typer.Option(
        None,
        "-f",
        "--format",
        case_sensitive=False,
        help="Report format (json or yaml).",
        callback=_format_callback,
    ),
    config: Optional[Path] = typer.Option(
        None,
        "-c",
        "-t",
        "--config",
        exists=True,
        dir_okay=False,
        readable=True,
        resolve_path=True,
        help="Choose config file (.yml or .json).",
    ),
) -> None:
    """Baygon functional test runner."""

    _ = _version  # Trigger callback evaluation & silence linters.

    runner_kwargs: Dict[str, Any] = {
        "executable": str(executable) if executable else None,
        "verbose": verbose,
        "limit": limit,
        "report": str(report) if report else None,
        "table": table,
        "pretty": pretty,
        "format": format,
        "config": str(config) if config else None,
    }

    if debug:
        logger.setLevel(logging.DEBUG)
        logger.debug("Debug mode enabled.")
        runner = Runner(**runner_kwargs)
        runner.run()
    else:
        try:
            runner = Runner(**runner_kwargs)
            runner.run()
        except InvalidExecutableError as error:
            typer.secho(f"\nError: {error}", fg="red", bold=True, err=True)
            raise typer.Exit(code=1) from error

    typer.echo("")


def run() -> None:
    """Entrypoint used by poetry script."""
    app()


if __name__ == "__main__":
    run()
