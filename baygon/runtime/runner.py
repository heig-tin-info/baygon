"""Pure runner built on top of Baygon domain models."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Iterator, Mapping, MutableMapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
import time
from typing import Any, Callable, Union

from baygon.core.models import CaseModel, ConditionModel, GroupModel, SuiteModel
from baygon.error import InvalidExecutableError
from baygon.executable import Executable, Outputs, get_env
from baygon.filters import FilterEval, FilterNone, Filters
from baygon.matchers import InvalidExitStatus, MatcherFactory


@dataclass(frozen=True)
class CommandLog:
    """Captured information about a single executed command."""

    argv: tuple[str, ...]
    stdin: str | None
    stdout: str
    stderr: str
    exit_status: int


@dataclass(frozen=True)
class CaseResult:
    """Individual case execution result."""

    case: CaseModel
    status: str
    issues: tuple[Any, ...]
    commands: tuple[CommandLog, ...]
    duration: float | None = None
    points_earned: float | int | None = None


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


FilterType = Filters
EvalType = Union[FilterNone, FilterEval]


@dataclass
class _ExecutionContext:
    filters: FilterType
    eval_filter: EvalType
    executable: str | None


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
    ) -> None:
        self._suite = suite
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
            points_total=points_total,
            points_earned=points_earned,
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
        if isinstance(node, CaseModel):
            context = _ExecutionContext(
                filters=_merge_filters(parent_context.filters, node.filters),
                eval_filter=_resolve_eval(parent_context.eval_filter, node.eval),
                executable=_inherit_executable(
                    parent_context.executable, node.executable, self._base_dir
                ),
            )
            yield (node, context)
            return

        context = _ExecutionContext(
            filters=_merge_filters(parent_context.filters, node.filters),
            eval_filter=_resolve_eval(parent_context.eval_filter, node.eval),
            executable=_inherit_executable(
                parent_context.executable, node.executable, self._base_dir
            ),
        )
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

        for _ in range(case.repeat):
            filtered_args = tuple(_apply_eval(eval_filter, list(case.args)))
            filtered_stdin = _apply_eval(eval_filter, case.stdin)
            filtered_env = _apply_eval_env(eval_filter, case.env)
            expected_exit = (
                int(_apply_eval(eval_filter, str(case.exit)))
                if case.exit is not None
                else None
            )

            hook = _capture_hook(command_logs)
            output = exec_obj.run(
                *filtered_args,
                stdin=filtered_stdin if filtered_stdin is not None else None,
                env=get_env(filtered_env),
                hook=hook,
            )

            issues.extend(
                _match_streams(
                    case,
                    filters,
                    eval_filter,
                    output,
                    "stdout",
                    case.stdout,
                )
            )
            issues.extend(
                _match_streams(
                    case,
                    filters,
                    eval_filter,
                    output,
                    "stderr",
                    case.stderr,
                )
            )

            if expected_exit is not None and expected_exit != output.exit_status:
                issues.append(
                    InvalidExitStatus(
                        expected_exit,
                        output.exit_status,
                        on="exit",
                        test=case,
                    )
                )

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
        )

    def _get_executable(self, path: str) -> Executable:
        if path not in self._executables:
            self._executables[path] = self._executable_factory(path)
        return self._executables[path]

    def _resolve_path(self, value: str | Path | None) -> str | None:
        if value is None:
            return None
        path = Path(value)
        if not path.is_absolute():
            path = (self._base_dir / path).resolve()
        return str(path)


def _inherit_executable(
    parent: str | None,
    child: str | None,
    base_dir: Path,
) -> str | None:
    if child is None:
        return parent
    if parent is not None:
        raise InvalidExecutableError("Executable can't be overridden")
    path = Path(child)
    if not path.is_absolute():
        path = (base_dir / path).resolve()
    return str(path)


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
    if value is None:
        return None
    if isinstance(eval_filter, FilterNone):
        return value
    return eval_filter(value)


def _apply_eval_env(eval_filter: EvalType, env: Mapping[str, Any]) -> dict[str, Any]:
    if not env:
        return {}
    return {key: _apply_eval(eval_filter, value) for key, value in env.items()}


def _capture_hook(storage: list[CommandLog]) -> Callable[..., None]:
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
) -> list[Any]:
    issues: list[Any] = []
    stream_value = getattr(output, stream_name)
    value = str(stream_value) if stream_value is not None else ""
    for condition in conditions:
        filters = _merge_filters(base_filters, condition.filters)
        filtered_value = filters(value)
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
    for matcher_name in ("equals", "regex", "contains"):
        expected = getattr(condition, matcher_name, None)
        if expected is not None:
            yield matcher_name, expected
