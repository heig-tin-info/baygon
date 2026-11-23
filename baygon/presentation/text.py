"""Plain-text presentation of Baygon run reports."""

from __future__ import annotations

from collections.abc import Callable

from baygon.helpers import display_command
from baygon.i18n import tr
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
            run = tr(
                "run {run} of {total}", run=result.failed_run, total=result.case.repeat
            )
            lines[0] += f"  # {run}"
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
        header = tr("Test {id}: {name}", id=result.case.id_str, name=result.case.name)
        status = result.status.lower()
        if status == "passed":
            write(f"{header} {tr('PASSED')}")
        elif status == "failed":
            write(f"{header} {tr('FAILED')}")
            if include_issues:
                for line in failure_details(result):
                    write(INDENT + line)
        elif status == "skipped":
            write(f"{header} {tr('SKIPPED')}")
        else:
            write(f"{header} {result.status}")


def render_summary(report: RunReport, *, write: Writer) -> None:
    """Render the global summary for a run."""

    write("")
    write(
        tr(
            "Ran {total} tests in {seconds:.2f} s.",
            total=report.total,
            seconds=report.duration,
        )
    )

    if report.points_total:
        write(
            tr(
                "Points: {earned}/{total}",
                earned=report.points_earned,
                total=report.points_total,
            )
        )

    if report.failures > 0:
        denominator = max(report.failures + report.successes, 1)
        ratio = round(100 - (report.failures / denominator) * 100, 2)
        write(
            tr(
                "{failures} failed, {successes} passed ({ratio}% ok).",
                failures=report.failures,
                successes=report.successes,
                ratio=ratio,
            )
        )
        write(tr("fail."))
    else:
        write(tr("ok."))

    if report.skipped > 0:
        write(
            tr(
                "{count} test(s) skipped, some executables may be missing.",
                count=report.skipped,
            )
        )
