"""Test suite."""

from __future__ import annotations

from pathlib import Path

from .config.loader import (
    discover_config,
    load_config as load_config_model,
    load_config_dict,
)
from .core.models import SuiteModel, build_suite_model
from .error import ConfigError, InvalidExecutableError
from .executable import Executable, get_env
from .filters import FilterEval, FilterNone, Filters
from .id import Id
from .matchers import InvalidExitStatus, MatcherFactory
from .runtime.runner import BaygonRunner
from .schema import Schema
from .score import compute_points


def find_testfile(path=None):
    """Recursively find the tests description file."""
    try:
        return discover_config(path)
    except ConfigError:
        return None


def load_config(path=None):
    """Load a configuration file (can be YAML or JSON)."""
    return load_config_dict(path)


class BaseMixin:
    """Base mixin to prevent super() failure.
    Ensure it will be the last MRO (Method Resolution Order).
    """

    def __init__(self, *args, **kwargs):
        self.parent = kwargs.get("parent")


class FilterMixin(BaseMixin):
    """Mixin for tests that can have filters."""

    def __init__(self, *args, **kwargs):
        config = args[0]

        # Configure filters (copy parent filters to avoid shared mutations)
        parent_filters = None
        if "parent" in kwargs and hasattr(kwargs["parent"], "filters"):
            parent_filters = kwargs["parent"].filters
        self.filters = Filters(parent_filters)

        if "filters" in config:
            self.filters.extend(config["filters"])

        # Eval
        if "parent" in kwargs and hasattr(kwargs["parent"], "eval"):
            self.eval = kwargs["parent"].eval
        else:
            self.eval = FilterNone()

        if isinstance(config.get("eval"), dict):
            self.eval = FilterEval(**config["eval"])

        super().__init__(*args, **kwargs)


class ExecutableMixin(BaseMixin):
    """Mixin for tests that have an executable."""

    def __init__(self, *args, **kwargs):
        config = args[0]
        self.cwd = kwargs["parent"].cwd

        if hasattr(kwargs["parent"], "executable"):
            executable = kwargs["parent"].executable
        else:
            executable = None

        if executable is not None and config["executable"] is not None:
            raise InvalidExecutableError("Executable can't be overridden")

        if config["executable"] is not None:
            exe = self.cwd.joinpath(config["executable"]).resolve(strict=True)
            self.executable = Executable(exe)
        else:
            self.executable = Executable(executable)

        super().__init__(*args, **kwargs)


class NamedMixin(BaseMixin):
    """Mixin for tests having a name."""

    def __init__(self, *args, **kwargs):
        config = args[0]

        self.name = config["name"]
        self.id = Id(config["test_id"])
        self.points = config.get("points", 1)

        super().__init__(*args, **kwargs)

    def __repr__(self):
        return f"{self.__class__.__name__}<{self.id}. {self.name}>"


class GroupMixin(BaseMixin):
    """Mixin for tests that can have sub-tests."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        config = args[0]
        self.tests = []
        for test in config["tests"]:
            if "tests" in test:
                self.tests.append(TestGroup(test, parent=self))
            else:
                self.tests.append(TestCase(test, parent=self))

    def __len__(self):
        return len(self.tests)

    def __getitem__(self, item):
        return self.tests[item]

    def run(self, flatten=False):
        """Run the tests."""
        if flatten:
            issues = []
            for test in self.tests:
                run = test.run()
                issues += run if isinstance(run, list) else [run]
        else:
            issues = [test.run() for test in self.tests]
        return issues

    def get_points(self):
        """Return the total number of points."""
        return sum(test.points for test in self.tests)


class TestCase(NamedMixin, ExecutableMixin, FilterMixin):
    """A single test."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        config = args[0]

        self.args = config.get("args", [])
        self.env = config.get("env", {})

        self.stdin = config.get("stdin", "")
        self.stdout = config.get("stdout", [])
        self.stderr = config.get("stderr", [])

        self.exit = config.get("exit", None)

        self.repeat = config.get("repeat", 1)

        self.config = config
        self.output = None
        self.issues = []

        self.filtered_args = None
        self.filtered_exit = None
        self.filtered_stdin = None
        self.filtered_env = None

    def _eval(self, data):
        if not self.eval:
            return data
        if isinstance(data, list):
            return [self.eval(arg) for arg in data]
        return self.eval(data)

    def run(self, hook=None):
        """Run the tests."""
        if not isinstance(self.executable, Executable):
            raise InvalidExecutableError(
                f"Test {self.id}, not a valid executable: {self.executable}"
            )

        self.issues = []
        for _ in range(self.repeat):
            self.filtered_args = self._eval(self.args)
            self.filtered_stdin = self._eval(self.stdin)
            self.filtered_env = self._eval_env()
            self.filtered_exit = (
                int(self._eval(str(self.exit))) if self.exit is not None else None
            )

            self.output = output = self.executable.run(
                *self.filtered_args,
                stdin=self.filtered_stdin,
                env=get_env(self.filtered_env),
                hook=hook,
            )

            for on in ["stdout", "stderr"]:
                for case in getattr(self, on):
                    self._match(on, case, output)
                    if "not" in case:  # Check for negative match
                        self._match(on, case["not"], output, inverse=True)

            if (
                self.filtered_exit is not None
                and self.filtered_exit != output.exit_status
            ):
                self.issues.append(
                    InvalidExitStatus(
                        self.filtered_exit, output.exit_status, on="exit", test=self
                    )
                )

        return self.issues

    def _match(self, on, case, output, inverse=False):
        """Match the output."""
        if "filters" in case:
            filters = Filters(self.filters).extend(case["filters"])
        else:
            filters = self.filters

        for key in MatcherFactory.matchers():
            if key in case:
                out = filters(getattr(output, on))
                matcher = MatcherFactory(key, self._eval(case[key]), inverse=inverse)
                issue = matcher(out, on=on, test=self)
                if issue:
                    self.issues.append(issue)

    def _eval_env(self):
        """Evaluate environment variables with the configured evaluator."""
        if not self.env:
            return {}
        if not self.eval:
            return dict(self.env)
        return {key: self.eval(value) for key, value in self.env.items()}


class TestGroup(NamedMixin, ExecutableMixin, FilterMixin, GroupMixin):
    """A group of tests."""


class TestSuite(ExecutableMixin, FilterMixin, GroupMixin):
    """Test suite."""

    __test__ = False  # Don't run this class as a test

    def __init__(
        self,
        data: dict | None = None,
        path: Path | str | None = None,
        executable: Path | str | None = None,
        cwd: Path | str | None = None,
    ):
        self.model: SuiteModel | None = None

        if isinstance(data, dict):
            self.config = Schema(data)
            compute_points(self.config)
            base_dir = Path(cwd) if cwd is not None else Path.cwd()
            self.model = build_suite_model(self.config)
        else:
            try:
                self.path = discover_config(path)
            except ConfigError as error:
                raise ConfigError(f"Couldn't find configuration file for '{path}'.") from error
            self.config = load_config_dict(self.path)
            base_dir = self.path.parent
            self.model = load_config_model(self.path)

        self.base_dir = Path(base_dir).resolve()
        self.runtime_runner = BaygonRunner(
            self.model,
            base_dir=self.base_dir,
            executable=executable,
        )

        self.name = self.config.get("name", "Test Suite")
        self.version = self.config.get("version")

        class Root:
            def __init__(self, executable, cwd):
                self.executable = Executable(executable)
                self.cwd = Path(cwd).resolve()

        super().__init__(self.config, parent=Root(executable, self.base_dir))
