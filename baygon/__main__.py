"""Main CLI command."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from pydantic import ValidationError
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
from .schema import _humanize_errors
from .skill import install_skill
from .suite import SuiteExecutor, SuiteLoader

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("baygon")

console = Console()
app = typer.Typer(
    help="Baygon functional test runner.",
    context_settings={"allow_interspersed_args": True},
)


def _report_payload(report: RunReport) -> dict:
    return report.as_dict()


def _split_ids(values: list[str] | None) -> list[str]:
    """Accept both ``--only 1 --only 2`` and ``--only 1,2``."""
    return [part for value in values or () for part in value.split(",") if part]


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


def _timeout_callback(value: float | None) -> float | None:
    if value is not None and value <= 0:
        raise typer.BadParameter("Timeout must be greater than 0.")
    return value


def _install_skill_callback(scope: str | None) -> None:
    if scope is None:
        return
    try:
        destination = install_skill(scope)
    except (OSError, FileExistsError) as error:
        typer.secho(f"Error: {error}", fg="red", bold=True, err=True)
        raise typer.Exit(code=1) from error
    typer.echo(f"Baygon skill installed in {destination}")
    typer.echo("Start a new Claude Code session to load it.")
    raise typer.Exit()


def _format_callback(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.lower()
    if normalized not in {"json", "yaml"}:
        raise typer.BadParameter("Format must be 'json' or 'yaml'.")
    return normalized


@app.callback(invoke_without_command=True)
def cli(
    executable: Path | None = typer.Argument(
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
    report: Path | None = typer.Option(
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
    report_format: str | None = typer.Option(
        None,
        "-f",
        "--format",
        case_sensitive=False,
        help="Report format (json or yaml).",
        callback=_format_callback,
    ),
    config: Path | None = typer.Option(
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
    only: list[str] | None = typer.Option(
        None,
        "--only",
        metavar="ID",
        help="Run only the tests whose id starts with ID (e.g. 2 or 2.1). "
        "Repeatable, or comma separated.",
    ),
    keyword: list[str] | None = typer.Option(
        None,
        "-k",
        "--keyword",
        metavar="TEXT",
        help="Run only the tests whose name, or group name, contains TEXT. "
        "Repeatable.",
    ),
    timeout: float | None = typer.Option(
        None,
        "--timeout",
        metavar="SECONDS",
        callback=_timeout_callback,
        help="Time limit of each test that sets none in the configuration.",
    ),
    strict: bool = typer.Option(
        False,
        "--strict",
        help="Exit with status 1 when a test fails.",
    ),
    _install_skill: str | None = typer.Option(
        None,
        "--install-skill",
        metavar="SCOPE",
        callback=_install_skill_callback,
        is_eager=True,
        help="Install the Baygon skill for Claude Code and exit: 'user' "
        "(~/.claude/skills), 'project' (./.claude/skills) or a skills directory.",
    ),
) -> None:
    """Baygon functional test runner."""

    del _version, _install_skill  # Handled by their callbacks.

    resolved_executable = str(executable) if executable else None

    loader = SuiteLoader()
    executor = SuiteExecutor()

    try:
        context = loader.load(path=str(config) if config else None)
    except ValidationError as error:
        typer.secho(
            f"\nError: invalid configuration\n{_humanize_errors(error)}",
            fg="red",
            bold=True,
            err=True,
        )
        raise typer.Exit(code=1) from error
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

    if only or keyword:
        try:
            context = context.select(ids=_split_ids(only), keywords=keyword)
        except ValueError as error:
            typer.secho(f"\nError: {error}", fg="red", bold=True, err=True)
            raise typer.Exit(code=1) from error
        if not context.model.tests:
            typer.secho("\nError: no test selected.", fg="red", bold=True, err=True)
            raise typer.Exit(code=1)

    try:
        report_result = executor.run(
            context,
            executable=resolved_executable,
            limit=limit,
            timeout=timeout,
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
            "yaml" if destination.endswith((".yaml", ".yml")) else "json"
        )
        save_report(_report_payload(report_result), destination, output_format)

    typer.echo("")

    if strict and report_result.failures > 0:
        raise typer.Exit(code=1)


def run() -> None:
    """Entrypoint used by packaging tools."""
    app()


if __name__ == "__main__":
    run()
