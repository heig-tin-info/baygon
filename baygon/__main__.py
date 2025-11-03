"""Main CLI command."""

# ruff: noqa: UP007

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

from rich.console import Console
import typer

from . import __copyright__, __version__
from .error import ConfigError, InvalidExecutableError
from .presentation.rich import (
    render_command_panels,
    render_pretty_failures,
    render_summary_table,
)
from .presentation.text import render_case_results, render_summary
from .runtime.runner import RunReport
from .suite import SuiteExecutor, SuiteLoader


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("baygon")

console = Console()
app = typer.Typer(
    help="Baygon functional test runner.",
    context_settings={"allow_interspersed_args": True},
)


def _report_payload(report: RunReport) -> dict:
    return {
        "failures": report.failures,
        "successes": report.successes,
        "skipped": report.skipped,
        "total": report.total,
        "time": report.duration,
        "points": {
            "total": report.points_total,
            "earned": report.points_earned,
        },
    }


def save_report(data, filename, output_format):
    """Save the report to a file."""
    if output_format == "json":
        with Path(filename).open("w", encoding="utf-8") as fp:
            json.dump(data, fp, indent=2, sort_keys=True)
    elif output_format == "yaml":
        import yaml

        with Path(filename).open("w", encoding="utf-8") as fp:
            yaml.dump(data, fp)


def version():
    """Display the version."""
    typer.echo(f"Baygon version {__version__} {__copyright__}")


def _version_callback(version_requested: bool) -> None:
    if version_requested:
        version()
        raise typer.Exit()


def _format_callback(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    normalized = value.lower()
    if normalized not in {"json", "yaml"}:
        raise typer.BadParameter("Format must be 'json' or 'yaml'.")
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
    report_format: Optional[str] = typer.Option(
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

    del _version  # Trigger callback evaluation & silence linters.

    resolved_executable = str(executable) if executable else None

    loader = SuiteLoader()
    executor = SuiteExecutor()

    try:
        context = loader.load(path=str(config) if config else None)
    except (ConfigError, ValueError) as error:
        typer.secho(f"\nError: {error}", fg="red", bold=True, err=True)
        raise typer.Exit(code=1) from error

    config_path = context.source_path or config
    typer.secho(f"Using configuration file: {config_path}")

    if verbose > 0:
        typer.echo(f"Verbose level set to {verbose}")

    if debug:
        logger.setLevel(logging.DEBUG)
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug mode enabled.")

    try:
        report_result = executor.run(
            context,
            executable=resolved_executable,
            limit=limit,
        )
    except InvalidExecutableError as error:
        typer.secho(f"\nError: {error}", fg="red", bold=True, err=True)
        raise typer.Exit(code=1) from error

    include_issues = not pretty
    render_case_results(
        report_result,
        write=typer.echo,
        verbose=verbose,
        include_issues=include_issues,
    )

    if verbose >= 3 and not pretty:
        for case_result in report_result.cases:
            render_command_panels(
                case_result,
                console=console,
                hide_empty_streams=False,
            )

    if pretty:
        render_pretty_failures(report_result, console=console)

    if table:
        render_summary_table(report_result, console=console)

    render_summary(report_result, write=typer.echo)

    if report:
        destination = str(report)
        output_format = report_format or (
            "yaml" if destination.endswith(".yaml") else "json"
        )
        save_report(_report_payload(report_result), destination, output_format)

    typer.echo("")


def run() -> None:
    """Entrypoint used by packaging tools."""
    app()


if __name__ == "__main__":
    run()
