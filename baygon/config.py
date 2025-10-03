"""
A Validated schema is modifed into a BaygonConfig in which:

- Points a computed from `weights` and `points` fields.
- Filters are converted into a Filters object.
- Tests are converted into a Tests object.
- Elements such as `executable`, `env`, `tty`, `timeout` are propagated to the tests.
- exectuable string is converted into Executable object.
"""

from .error import InvalidExecutableError
from .eval import Kernel
from .executable import Executable
from .filters import FilterNone, Filters
from .matchers import InvalidExitStatus, MatcherFactory
from .schema import SchemaConfig
from .score import assign_points
from .suite import ExecutableMixin, FilterMixin, NamedMixin

class BaygonConfig:
    def __init__(self, data):
        self.data = SchemaConfig(data)

        assign_points(self.data)

        context = {
            'executable': None,
            'env': {},
            'tty': False,
            'timeout': -1,
            'filters': Filters(),
            'cwd': None,
        }
        self._traverse(self.data["tests"], context)

    def _traverse(self, data, context):
        if "executable" in data:
            context['executable'] = Executable(data["executable"])
        if "filters" in data:
            data["filters"] = Filters(data["filters"])
        if "tests" in data:
            self._traverse(data["tests"], context.copy())
        if "tests" not in data:
            pass  # This is a leaf node (test case)


class TestCase(NamedMixin, ExecutableMixin, FilterMixin):
    """A single test."""

    def __init__(self, config, *args, **kwargs):
        super().__init__(config, *args, **kwargs)

        self.args = config.get("args", [])
        self.env = config.get("env", {})
        self.tty = config.get("tty", False)
        self.timeout = config.get("timeout", -1)

        self.stdin = config.get("stdin", "")
        self.stdout = config.get("stdout", [])
        self.stderr = config.get("stderr", [])

        self.exit = config.get("exit", None)

        self.outputs = {}
        self.issues = []

        self.filtered_args = None
        self.filtered_exit = None
        self.filtered_stdin = None

        self.filters = Filters(config.get("filters", {}))

        # Ensure executable has been set
        self.executable = config.get("executable", None)
        if not isinstance(self.executable, Executable):
            raise InvalidExecutableError(
                f"Test {self.id}, not a valid executable: {self.executable}"
            )

        self.kernel = (
            config.get("kernel", Kernel()) if config.get("eval", False) else None
        )

        self.extra = kwargs



    def run(self, hook=None):
        """Run the tests."""

        # Preprocess inputs data and expected outputs
        self.filtered_args = self._preprocess(self.args)
        self.filtered_stdin = self._preprocess(self.stdin)
        self.filtered_exit = (
            int(self._preprocess(str(self.exit))) if self.exit is not None else None
        )

        # Run the executable and collect the outputs
        self.outputs = output = self.executable.run(
            *self.filtered_args,
            stdin=self.filtered_stdin,
            hook=hook,
            env=self.env,
            tty=self.tty,
            timeout=self.timeout,
        )

        for on in ["stdout", "stderr"]:
            for case in getattr(self, on):
                self._match(on, case, output)
                if "not" in case:  # Check for negative match
                    self._match(on, case["not"], output, inverse=True)

        self.issues = []
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

    def _preprocess(self, data):
        """If inline evaluation using mustache syntax is enabled, evaluate data.

        It is used process args and stdin fields against matchers.
        """
        if not self.kernel:
            return data
        if isinstance(data, list):
            return [self.kernel.eval(arg) for arg in data]
        return self.kernel.eval(data)

    def _match(self, on, case, output, inverse=False):
        """Match the output."""
        if "filters" in case:
            filters = self.filters.extend(case["filters"])
        else:
            filters = FilterNone

        for key in MatcherFactory.matchers():
            if key in case:
                out = filters(getattr(output, on))
                matcher = MatcherFactory(
                    key, self._preprocess(case[key]), inverse=inverse
                )
                issue = matcher(out, on=on, test=self)
                if issue:
                    self.issues.append(issue)
