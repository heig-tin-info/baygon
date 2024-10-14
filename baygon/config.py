"""
A Validated schema is modifed into a BaygonConfig in which:

- Points a computed from `weights` and `points` fields.
- Filters are converted into a Filters object.
- Tests are converted into a Tests object.
- Elements such as `executable`, `env`, `tty`, `timeout` are propagated to the tests.
- exectuable string is converted into Executable object.
"""

from .schema import SchemaConfig
from .filters import Filters
from .matchers import MatcherFactory
from .executables import Executable
from .score import assign_points


class BaygonConfig:
    def __init__(self, data):
        self.data = SchemaConfig(data)

        assign_points(self.data)

    def _traverse(self, data):
        if "executable" in data:
            data["executable"] = Executable(data["executable"])
        if "filters" in data:
            data["filters"] = Filters(data["filters"])
        if "tests" in data:
            self._traverse(data["tests"])
