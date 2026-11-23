"""Plain-text presentation of Baygon run reports."""

from __future__ import annotations

from collections.abc import Callable

from baygon.helpers import display_command
from baygon.runtime.runner import CaseResult, RunReport

Writer = Callable[[str], None]

INDENT = "    "


def failure_details(result: CaseResult) -> list[str]:
    """Lines explaining why a test failed, for a student.

    The command to run it again comes first, then the explanations written by
    the author of the test, each followed by the issue it explains.
    """
    lines: list[str] = []
    command = result.command
    if command is not None:
        lines.extend(display_command(command.argv, command.stdin))
        if result.failed_run is not None and result.case.repeat > 1:
            lines[0] += f"  # run {result.failed_run} of {result.case.repeat}"
    if result.message:
        lines.append(result.message)
    for issue in result.issues:
        message = getattr(issue, "message", None)
        if message and message != result.message:
            lines.append(message)
        lines.extend(str(issue).splitlines())
    return lines


def render_case_results(
    report: RunReport,
    *,
    write: Writer,
    verbose: int = 0,
    include_issues: bool = True,
) -> None:
    """Render individual case outcomes."""

    del verbose  # Reserved for future verbosity handling.

    for result in report.cases:
        header = f"Test {result.case.id_str}: {result.case.name}"
        status = result.status.lower()
        if status == "passed":
            write(f"{header} PASSED")
        elif status == "failed":
            write(f"{header} FAILED")
            if include_issues:
                for line in failure_details(result):
                    write(INDENT + line)
        elif status == "skipped":
            write(f"{header} SKIPPED")
        else:
            write(f"{header} {result.status}")


def render_summary(report: RunReport, *, write: Writer) -> None:
    """Render the global summary for a run."""

    write("")
    write(f"Ran {report.total} tests in {report.duration:.2f} s.")

    if report.points_total:
        write(f"Points: {report.points_earned}/{report.points_total}")

    if report.failures > 0:
        denominator = max(report.failures + report.successes, 1)
        ratio = round(100 - (report.failures / denominator) * 100, 2)
        write(f"{report.failures} failed, {report.successes} passed ({ratio}% ok).")
        write("fail.")
    else:
        write("ok.")

    if report.skipped > 0:
        write(f"{report.skipped} test(s) skipped, some executables may be missing.")
