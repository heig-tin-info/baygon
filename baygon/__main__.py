"""Main CLI command."""

import logging
import os
import sys
import time

import click
from rich.box import SQUARE_DOUBLE_HEAD
from rich.console import Console
from rich.rule import Rule
from rich.style import Style
from rich.table import Table

from . import TestCase, TestGroup, TestSuite, __copyright__, __version__
from .error import InvalidExecutableError
from .helpers import create_command_line

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("baygon")

console = Console()


def display_pad(pad=0):
    """Display a pad of spaces to align nested output."""
    click.secho("." * pad if pad > 0 else "  ", nl=False, dim=pad == 0)


def test_name_length(test):
    """Compute the length of test name."""
    return len(f"{test.id.pad()}Test {test.id}: {test.name}")


def display_test_name(test):
    """Display the name of a test."""
    click.secho(f"{test.id.pad()}Test {test.id}: ", nl=False, bold=True)
    click.secho(f"{test.name}", nl=False, bold=False)


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
        if test.get("status") is not None:
            status = "[green]PASS[/green]" if test["status"] else "[red]FAIL[/red]"

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
        click.secho(f"Using configuration file: {config}")
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
        if self.verbose > 0:
            click.echo("Verbose level set to " + str(self.verbose))

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
            click.secho(
                f"Points: {self.points_earned}/{self.points_total}",
                bold=True,
            )

        if self.failures > 0:
            ratio = 100 - round(
                self.failures / (self.failures + self.successes) * 100, 2
            )
            click.secho(
                (f"{self.failures} failed, {self.successes} " f"passed ({ratio}% ok)."),
                fg="yellow",
                bold=True,
            )
            click.secho("\nfail.", fg="red", bold=True)
        else:
            click.secho("\nok.", fg="green")

        if self.skipped > 0:
            click.secho(
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
        cin = f' <<< "{stdin.decode("utf-8")}"' if stdin else ""
        self.ran_commands.append(
            f"{cmdline}{cin} (exited with: {exit_status})\n{stdout}{stderr}"
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
        name = []
        while True:
            if p is None or getattr(p, "name", None) is None:
                break
            if p.name:
                name.append(p.name)
            p = p.parent
        name = " / ".join(reversed(name))

        if verbose >= 2:
            console.print("\n")
            console.print(Rule(f"Test {test.id}: {name}", align="left", style="bold"))

        if verbose >= 3:
            click.secho(
                self.pad("".join([f"$ {cmd}\n" for cmd in self.ran_commands]), 2),
                dim=True,
            )

        if test.status == "skipped":
            if verbose > 0:
                click.secho(" SKIPPED", fg="yellow")
            else:
                click.secho("S", fg="yellow", nl=False)
            self.skipped += 1
            return

        if test.status == "passed":
            if verbose > 0:
                click.secho(" PASSED", fg="green")
            else:
                click.secho(".", fg="green", nl=False)
            self.successes += 1
            return

        if test.status == "failed":
            if verbose > 0:
                click.secho(" FAILED", fg="red")
            else:
                click.secho("F", fg="red", nl=False)
            self.failures += 1

        for k, issue in enumerate(issues):
            click.secho(str(issue))

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


@click.command()
@click.argument("executable", required=False, type=click.Path(exists=True))
@click.option("--version", is_flag=True, help="Shows version")
@click.option("-v", "--verbose", count=True, help="Shows more details")
@click.option("-l", "--limit", type=int, default=-1, help="Limit errors to N")
@click.option("-d", "--debug", is_flag=True, default=False, help="Debug mode")
@click.option("-r", "--report", type=click.Path(), help="Report file")
@click.option("-t", "--table", is_flag=True, default=False, help="Summary table")
@click.option(
    "-f", "--format", type=click.Choice(["json", "yaml"]), help="Report format"
)
@click.option(
    "-c",
    "--config",
    type=click.Path(exists=True),
    help="Choose config file (.yml or .json)",
)
def cli(debug, **kwargs):
    """Baygon functional test runner."""
    if kwargs.get("version"):
        version()
        sys.exit(0)

    if debug:
        logger.setLevel(logging.DEBUG)
        logger.debug("Debug mode enabled.")
        runner = Runner(**kwargs)
        runner.run()
    else:
        try:
            runner = Runner(**kwargs)
            runner.run()
        except InvalidExecutableError as error:
            click.secho(f"\nError: {error}", fg="red", bold=True, err=True)
            sys.exit(1)

    click.echo("")


if __name__ == "__main__":
    cli()
