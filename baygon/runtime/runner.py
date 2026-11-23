"""Pure runner built on top of Baygon domain models."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import (
    Callable,
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    Sequence,
)
from dataclasses import dataclass, replace
import os
from pathlib import Path
import shutil
import time
from typing import Any

from baygon.core.models import CaseModel, ConditionModel, GroupModel, SuiteModel
from baygon.error import InvalidExecutableError
from baygon.executable import DEFAULT_MAX_OUTPUT, Executable, Outputs, get_env
from baygon.filters import FilterEval, FilterNone, Filters
from baygon.matchers import (
    ExecutionFailed,
    ExecutionTimeout,
    HelperProgramFailed,
    InvalidExitStatus,
    InvalidSameAs,
    InvalidTestDefinition,
    MatcherFactory,
    OutputLimitExceeded,
)
from baygon.score import float_or_int


@dataclass(frozen=True)
class CommandLog:
    """Captured information about a single executed command."""

    argv: tuple[str, ...]
    stdin: str | None
    stdout: str
    stderr: str
    exit_status: int
    timed_out: bool = False
    output_limit_exceeded: bool = False
    #: ``None`` for the program under test, ``"generator"`` or ``"reference"``
    #: for the programs a test uses to build its input or expected output.
    role: str | None = None


@dataclass(frozen=True)
class CaseResult:
    """Individual case execution result."""

    case: CaseModel
    status: str
    issues: tuple[Any, ...]
    commands: tuple[CommandLog, ...]
    duration: float | None = None
    points_earned: float | int | None = None
    #: Explanation written by the author of the test, shown when it fails.
    message: str | None = None
    #: Run (from 1) of a repeated test that failed; the next runs are skipped.
    failed_run: int | None = None

    @property
    def command(self) -> CommandLog | None:
        """The last run of the program under test."""
        programs = [log for log in self.commands if log.role is None]
        return programs[-1] if programs else None

    @property
    def messages(self) -> list[str]:
        """Explanations of the failure written by the author of the test."""
        found: list[str] = []
        for text in (self.message, *(getattr(i, "message", None) for i in self.issues)):
            if text and text not in found:
                found.append(text)
        return found


@dataclass(frozen=True)
class RunReport:
    """Aggregated information after running a suite."""

    suite: SuiteModel
    successes: int
    failures: int
    skipped: int
    points_total: float | int
    points_earned: float | int
    duration: float
    cases: tuple[CaseResult, ...]

    @property
    def total(self) -> int:
        return self.successes + self.failures + self.skipped

    def as_dict(self, *, details: bool = True) -> dict[str, Any]:
        """Return the report as plain data, ready to be saved as JSON or YAML.

        With ``details``, the result of every test is listed under ``cases``
        and the subtotal of every group under ``groups``.
        """
        data: dict[str, Any] = {
            "failures": self.failures,
            "successes": self.successes,
            "skipped": self.skipped,
            "total": self.total,
            "time": self.duration,
            "points": {"total": self.points_total, "earned": self.points_earned},
        }
        if details:
            data["cases"] = [_case_payload(result) for result in self.cases]
            data["groups"] = _groups_payload(self.suite, self.cases)
        return data


def _round_points(value: float | int) -> float | int:
    """Remove the float noise of a sum of points (0.1 + 0.2 -> 0.3)."""
    return float_or_int(round(value, 9))


def _case_payload(result: CaseResult) -> dict[str, Any]:
    case = result.case
    payload = {
        "id": case.id_str,
        "name": case.name,
        "status": result.status,
        "points": {
            "total": case.points or 0,
            "earned": result.points_earned or 0,
        },
        "time": result.duration,
        "issues": [str(issue) for issue in result.issues],
    }
    if result.messages:
        payload["messages"] = result.messages
    if result.failed_run is not None and case.repeat > 1:
        payload["failed_run"] = result.failed_run
    return payload


def _groups_payload(
    suite: SuiteModel, results: Sequence[CaseResult]
) -> list[dict[str, Any]]:
    by_id = {result.case.id: result for result in results}
    groups: list[dict[str, Any]] = []

    def _walk(nodes: Iterable[CaseModel | GroupModel]) -> None:
        for node in nodes:
            if not isinstance(node, GroupModel):
                continue
            ran = [by_id[case.id] for case in node.iter_cases() if case.id in by_id]
            if ran:
                counts = defaultdict(int)
                for result in ran:
                    counts[result.status] += 1
                groups.append(
                    {
                        "id": ".".join(str(part) for part in node.id),
                        "name": node.name,
                        "successes": counts["passed"],
                        "failures": counts["failed"],
                        "skipped": counts["skipped"],
                        "total": len(ran),
                        "points": {
                            "total": _round_points(
                                sum(r.case.points or 0 for r in ran)
                            ),
                            "earned": _round_points(
                                sum(r.points_earned or 0 for r in ran)
                            ),
                        },
                    }
                )
            _walk(node.tests)

    _walk(suite.tests)
    return groups


FilterType = Filters
EvalType = FilterNone | FilterEval


@dataclass
class _ExecutionContext:
    filters: FilterType
    eval_filter: EvalType
    executable: str | None
    timeout: float | None = None
    max_output: int | None = None
    message: str | None = None


class BaygonRunner:
    """Execute suites described by immutable models."""

    def __init__(
        self,
        suite: SuiteModel,
        *,
        base_dir: Path,
        executable: str | Path | None = None,
        executable_factory: Callable[[str], Executable] = Executable,
        clock: Callable[[], float] = time.perf_counter,
        timeout: float | None = None,
        max_output: int | None = None,
    ) -> None:
        """Create a runner.

        Args:
            suite: The suite to run.
            base_dir: Directory relative executables are resolved from.
            executable: Executable given on the command line, if any.
            executable_factory: Builds the object that runs a program.
            clock: Clock used to measure durations.
            timeout: Time limit in seconds for the tests that do not set one
                in the configuration (``None``: no limit).
            max_output: Size limit in bytes of each output stream for the
                tests that do not set one in the configuration.
        """
        self._suite = suite
        self._default_timeout = timeout
        self._default_max_output = max_output
        self._base_dir = base_dir
        self._clock = clock
        self._executable_factory = executable_factory
        self._executables: MutableMapping[str, Executable] = {}

        cli_executable = self._resolve_path(executable)
        suite_executable = self._resolve_path(suite.executable)
        if cli_executable and suite_executable:
            raise InvalidExecutableError("Executable can't be overridden")
        self._root_executable = cli_executable or suite_executable

    @property
    def suite(self) -> SuiteModel:
        """Return the suite model handled by the runner."""
        return self._suite

    def run(self, limit: int = -1) -> RunReport:
        """Run the test suite."""
        results: list[CaseResult] = []
        counters = defaultdict(int)
        points_total: float | int = 0
        points_earned: float | int = 0

        start = self._clock()
        root_context = _ExecutionContext(
            filters=_merge_filters(None, self._suite.filters),
            eval_filter=_resolve_eval(None, self._suite.eval),
            executable=self._root_executable,
            timeout=_first_set(self._suite.timeout, self._default_timeout),
            max_output=_first_set(self._suite.max_output, self._default_max_output),
        )

        stop_requested = False

        for case, context in self._iter_cases(root_context):
            if stop_requested:
                break

            case_points = case.points or 0
            points_total += case_points
            case_result = self._run_case(case, context)

            results.append(case_result)
            status = case_result.status
            counters[status] += 1
            if status == "passed":
                points_earned += case_result.points_earned or 0
            elif status == "failed" and limit > 0 and counters["failed"] > limit:
                stop_requested = True

        duration = round(self._clock() - start, 6)
        return RunReport(
            suite=self._suite,
            successes=counters["passed"],
            failures=counters["failed"],
            skipped=counters["skipped"],
            points_total=_round_points(points_total),
            points_earned=_round_points(points_earned),
            duration=duration,
            cases=tuple(results),
        )

    def _iter_cases(
        self, root: _ExecutionContext
    ) -> Iterator[tuple[CaseModel, _ExecutionContext]]:
        for test in self._suite.tests:
            yield from self._walk(test, root)

    def _walk(
        self,
        node: CaseModel | GroupModel,
        parent_context: _ExecutionContext,
    ) -> Iterator[tuple[CaseModel, _ExecutionContext]]:
        context = _ExecutionContext(
            filters=_merge_filters(parent_context.filters, node.filters),
            eval_filter=_resolve_eval(parent_context.eval_filter, node.eval),
            executable=_inherit_executable(
                parent_context.executable, node.executable, self._base_dir
            ),
            timeout=_first_set(node.timeout, parent_context.timeout),
            max_output=_first_set(node.max_output, parent_context.max_output),
            message=_first_set(node.message, parent_context.message),
        )
        if isinstance(node, CaseModel):
            yield (node, context)
            return

        for child in node.tests:
            yield from self._walk(child, context)

    def _run_case(self, case: CaseModel, context: _ExecutionContext) -> CaseResult:
        start = self._clock()
        issues: list[Any] = []
        command_logs: list[CommandLog] = []
        exec_path = context.executable
        if exec_path is None:
            raise InvalidExecutableError(
                f"Executable not provided for test '{case.name}' (id {case.id_str})."
            )

        exec_obj = self._get_executable(exec_path)
        filters = context.filters
        eval_filter = context.eval_filter
        generator = case.stdin_command
        run = 0

        # A repeated test stops at its first failing run: the student sees one
        # failure, with the inputs that caused it, instead of hundreds.
        while run < case.repeat and not issues:
            run += 1
            try:
                filtered_args = tuple(_apply_eval(eval_filter, list(case.args)))
                filtered_stdin = _apply_eval(eval_filter, case.stdin)
                filtered_env = get_env(_apply_eval_env(eval_filter, case.env))
                expected_exit = _expected_exit(eval_filter, case.exit)
                generator_args = (
                    tuple(_apply_eval(eval_filter, list(generator.args)))
                    if generator is not None
                    else ()
                )
            except Exception as error:
                issues.append(InvalidTestDefinition(error, None, test=case))
                break

            if generator is not None:
                try:
                    filtered_stdin = self._run_helper(
                        "generator",
                        generator.executable,
                        generator_args,
                        stdin=None,
                        env=filtered_env,
                        context=context,
                        logs=command_logs,
                    ).stdout
                except _HelperProgramError as failure:
                    issues.append(failure.to_issue(case))
                    break

            hook = _capture_hook(command_logs)
            try:
                output = exec_obj.run(
                    *filtered_args,
                    stdin=filtered_stdin,
                    env=filtered_env,
                    hook=hook,
                    **_limits(context),
                )
            except OSError as error:
                issues.append(ExecutionFailed(error, exec_path, on="exit", test=case))
                break

            timed_out = bool(getattr(output, "timed_out", False))
            overflow = bool(getattr(output, "output_limit_exceeded", False))
            if (timed_out or overflow) and command_logs:
                command_logs[-1] = replace(
                    command_logs[-1],
                    timed_out=timed_out,
                    output_limit_exceeded=overflow,
                )
            if timed_out:
                issues.append(
                    ExecutionTimeout(output, context.timeout, on="exit", test=case)
                )
                break
            if overflow:
                limit = context.max_output or DEFAULT_MAX_OUTPUT
                issues.append(OutputLimitExceeded(output, limit, on="exit", test=case))
                break

            references: dict[str, Outputs] = {}

            def _reference(
                path: str,
                args: tuple[str, ...] = filtered_args,
                stdin: str | None = filtered_stdin,
                env: dict[str, Any] = filtered_env,
                cache: dict[str, Outputs] = references,
            ) -> Outputs:
                if path not in cache:
                    cache[path] = self._run_helper(
                        "reference",
                        path,
                        args,
                        stdin=stdin,
                        env=env,
                        context=context,
                        logs=command_logs,
                    )
                return cache[path]

            try:
                for stream in ("stdout", "stderr"):
                    issues.extend(
                        _match_streams(
                            case,
                            filters,
                            eval_filter,
                            output,
                            stream,
                            getattr(case, stream),
                            reference=_reference,
                        )
                    )
            except _HelperProgramError as failure:
                issues.append(failure.to_issue(case))
                break
            except Exception as error:
                issues.append(InvalidTestDefinition(error, None, test=case))
                break

            if expected_exit is not None and expected_exit != output.exit_status:
                issue = InvalidExitStatus(
                    expected_exit,
                    output.exit_status,
                    on="exit",
                    test=case,
                )
                issue.message = _explain(eval_filter, case.exit_message, issues, case)
                issues.append(issue)

        message = None
        if issues:
            message = _explain(eval_filter, context.message, issues, case)
        status = "failed" if issues else "passed"
        duration = round(self._clock() - start, 6)
        points = case.points or 0
        earned = points if status == "passed" else 0

        return CaseResult(
            case=case,
            status=status,
            issues=tuple(issues),
            commands=tuple(command_logs),
            duration=duration,
            points_earned=earned,
            message=message,
            failed_run=run if issues else None,
        )

    def _run_helper(
        self,
        role: str,
        path: str,
        args: Sequence[str],
        *,
        stdin: str | None,
        env: dict[str, Any],
        context: _ExecutionContext,
        logs: list[CommandLog],
    ) -> Outputs:
        """Run a generator or reference program used by a test."""
        label = f"{role.capitalize()} {path}"
        try:
            program = self._get_executable(self._resolve_path(path))
            output = program.run(
                *args,
                stdin=stdin,
                env=env,
                hook=_capture_hook(logs, role=role),
                **_limits(context),
            )
        except (OSError, InvalidExecutableError) as error:
            raise _HelperProgramError(label, str(error)) from error
        if getattr(output, "timed_out", False):
            raise _HelperProgramError(label, f"timeout after {context.timeout:g} s")
        if getattr(output, "output_limit_exceeded", False):
            raise _HelperProgramError(label, "output limit exceeded")
        if role == "generator" and output.exit_status != 0:
            raise _HelperProgramError(label, f"exit status {output.exit_status}")
        return output

    def _get_executable(self, path: str) -> Executable:
        if path not in self._executables:
            self._executables[path] = self._executable_factory(path)
        return self._executables[path]

    def _resolve_path(self, value: str | Path | None) -> str | None:
        return _resolve_executable(value, self._base_dir)


class _HelperProgramError(Exception):
    """A generator or reference program failed."""

    def __init__(self, label: str, reason: str) -> None:
        super().__init__(f"{label} failed: {reason}")
        self.label = label
        self.reason = reason

    def to_issue(self, case: CaseModel) -> HelperProgramFailed:
        return HelperProgramFailed(self.reason, self.label, on="exit", test=case)


def _limits(context: _ExecutionContext) -> dict[str, Any]:
    """Limits to pass to ``run``, only when set.

    A custom executable whose ``run`` does not know them keeps working.
    """
    limits: dict[str, Any] = {}
    if context.timeout is not None:
        limits["timeout"] = context.timeout
    if context.max_output is not None:
        limits["max_output"] = context.max_output
    return limits


def _explain(
    eval_filter: EvalType,
    message: str | None,
    issues: list[Any],
    case: CaseModel,
) -> str | None:
    """Evaluate an explanation written by the author of the test.

    Its ``{{ }}`` expressions see the values of the failing run. An expression
    that cannot be evaluated adds an issue and leaves the text as it is.
    """
    if message is None:
        return None
    try:
        return str(_apply_eval(eval_filter, message))
    except Exception as error:
        issues.append(InvalidTestDefinition(error, None, test=case))
        return message


def _expected_exit(eval_filter: EvalType, value: int | str | None) -> int | None:
    if value is None:
        return None
    evaluated = _apply_eval(eval_filter, str(value))
    try:
        return int(evaluated)
    except ValueError:
        raise ValueError(f"exit must be an integer, got '{evaluated}'") from None


def _first_set(*values: Any) -> Any:
    """Return the first value that is not ``None``."""
    return next((value for value in values if value is not None), None)


def _inherit_executable(
    parent: str | None,
    child: str | None,
    base_dir: Path,
) -> str | None:
    """Return the executable of a node: its own one if set, else the parent's."""
    if child is None:
        return parent
    return _resolve_executable(child, base_dir)


def _resolve_executable(value: str | Path | None, base_dir: Path) -> str | None:
    """Resolve an executable given in the configuration.

    A relative path is relative to ``base_dir`` (the directory of the
    configuration file). A bare name such as ``grep`` that is not a file in
    ``base_dir`` is looked up in the ``PATH``.
    """
    if value is None:
        return None
    path = Path(value)
    if path.is_absolute():
        return str(path)
    resolved = (base_dir / path).resolve()
    name = str(value)
    if (
        not resolved.exists()
        and "/" not in name
        and os.sep not in name
        and shutil.which(name) is not None
    ):
        return name  # Found in the PATH by Executable.
    return str(resolved)


def _merge_filters(
    parent: FilterType | None, current: Mapping[str, Any] | None
) -> FilterType:
    filters = Filters(parent) if parent is not None else Filters()
    if current:
        filters.extend(dict(current))
    return filters


def _resolve_eval(
    parent: EvalType | None, current: Mapping[str, Any] | None
) -> EvalType:
    if current:
        return FilterEval(**dict(current))
    if parent is not None:
        return parent
    return FilterNone()


def _apply_eval(eval_filter: EvalType, value: Any) -> Any:
    if isinstance(value, list):
        return [_apply_eval(eval_filter, item) for item in value]
    if isinstance(value, tuple):
        return tuple(_apply_eval(eval_filter, item) for item in value)
    if isinstance(value, Mapping):
        return {key: _apply_eval(eval_filter, item) for key, item in value.items()}
    if value is None:
        return None
    if isinstance(eval_filter, FilterNone) or not isinstance(value, str):
        return value
    return eval_filter(value)


def _apply_eval_env(eval_filter: EvalType, env: Mapping[str, Any]) -> dict[str, Any]:
    if not env:
        return {}
    return {key: _apply_eval(eval_filter, value) for key, value in env.items()}


def _capture_hook(
    storage: list[CommandLog], role: str | None = None
) -> Callable[..., None]:
    def _hook(**kwargs: Any) -> None:
        cmd = tuple(str(arg) for arg in kwargs.get("cmd", ()))
        stdin = kwargs.get("stdin")
        if isinstance(stdin, (bytes, bytearray)):
            stdin_value = stdin.decode("utf-8", errors="replace")
        else:
            stdin_value = stdin
        stdout_value = kwargs.get("stdout")
        stderr_value = kwargs.get("stderr")
        storage.append(
            CommandLog(
                argv=cmd,
                stdin=stdin_value,
                stdout="" if stdout_value is None else str(stdout_value),
                stderr="" if stderr_value is None else str(stderr_value),
                exit_status=int(kwargs.get("exit_status", 0)),
                role=role,
            )
        )

    return _hook


def _match_streams(
    case: CaseModel,
    base_filters: FilterType,
    eval_filter: EvalType,
    output: Outputs,
    stream_name: str,
    conditions: Sequence[ConditionModel],
    *,
    reference: Callable[[str], Outputs],
) -> list[Any]:
    issues: list[Any] = []
    stream_value = getattr(output, stream_name)
    value = str(stream_value) if stream_value is not None else ""
    for condition in conditions:
        first = len(issues)
        filters = _merge_filters(base_filters, condition.filters)
        filtered_value = filters(value)
        if condition.same_as is not None:
            reference_output = getattr(reference(condition.same_as), stream_name)
            expected = filters(str(reference_output or ""))
            if filtered_value != expected:
                issues.append(
                    InvalidSameAs(
                        filtered_value,
                        expected,
                        reference=condition.same_as,
                        on=stream_name,
                        test=case,
                    )
                )
        issues.extend(
            _evaluate_condition(
                _iter_condition_expectations(condition),
                filtered_value,
                stream_name,
                case,
                inverse=False,
                eval_filter=eval_filter,
            )
        )
        for negated in condition.negated:
            issues.extend(
                _evaluate_condition(
                    _iter_condition_expectations(negated),
                    filtered_value,
                    stream_name,
                    case,
                    inverse=True,
                    eval_filter=eval_filter,
                )
            )
        if condition.message is not None and len(issues) > first:
            message = str(_apply_eval(eval_filter, condition.message))
            for issue in issues[first:]:
                issue.message = message
    return issues


def _evaluate_condition(
    expectations: Iterable[tuple[str, str]],
    value: str,
    stream_name: str,
    case: CaseModel,
    *,
    inverse: bool,
    eval_filter: EvalType,
) -> list[Any]:
    issues: list[Any] = []
    for matcher_name, expected in expectations:
        evaluated = _apply_eval(eval_filter, expected)
        matcher = MatcherFactory(
            matcher_name,
            evaluated,
            inverse=inverse,
        )
        issue = matcher(value, on=stream_name, test=case)
        if issue:
            issues.append(issue)
    return issues


def _iter_condition_expectations(
    condition: ConditionModel | Any,
) -> Iterator[tuple[str, str]]:
    for matcher_name in ("equals", "regex", "contains", "number", "length", "lines"):
        expected = getattr(condition, matcher_name, None)
        if expected is not None:
            yield matcher_name, expected
