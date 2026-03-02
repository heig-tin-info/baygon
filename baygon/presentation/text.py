"""Plain-text presentation of Baygon run reports."""

from __future__ import annotations

from typing import Callable

from baygon.runtime.runner import RunReport

Writer = Callable[[str], None]


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
            if include_issues and result.issues:
                for issue in result.issues:
                    write(str(issue))
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
        ratio = 100 - round((report.failures / denominator) * 100, 2)
        write(f"{report.failures} failed, {report.successes} passed ({ratio}% ok).")
        write("fail.")
    else:
        write("ok.")

    if report.skipped > 0:
        write(f"{report.skipped} test(s) skipped, some executables may be missing.")
