"""YAML Schema for Baygon test files."""

from voluptuous import (
    All,
    Any,
    Boolean,
    Coerce,
    ExactSequence,
    Exclusive,
    Optional,
    Required,
    Schema,
    Self,
)
from voluptuous.humanize import validate_with_humanized_errors

from .id import TrackId

Value = Any(str, All(Any(int, float, All(bool, Coerce(int))), Coerce(str)))


class ToList:
    """Convert the given value to a list."""

    def __call__(self, v):
        return [v]


class ToDict:
    """Convert the given value to a dict."""

    def __init__(self, key):
        self.key = key

    def __call__(self, v):
        return {self.key: v}


class Join:
    """Join the given values."""

    def __init__(self, sep):
        self.sep = sep

    def __call__(self, v):
        return self.sep.join(v)


evaluate = {
    Optional("eval", description="Eval mustaches"): Any(
        {
            Optional(
                "start", default="{{", description="Start of the mustache delimiter"
            ): str,
            Optional(
                "end", default="}}", description="End of the mustache delimiter"
            ): str,
            Optional(
                "init", default="", description="Evaluation kernel start code"
            ): Any(All(str, ToList()), [str]),
        },
        All(Any(Boolean(), None), lambda x: {"init": []}),
    )
}

# Global test filters
filters = {
    Optional("uppercase"): Boolean(),
    Optional("lowercase"): Boolean(),
    Optional("trim"): Boolean(),
    Optional(Any("stripall", "strip-all", "ignorespaces", "ignore-spaces")): Boolean(),
    Optional("regex"): Any(
        ExactSequence([str, str]),
        {"pattern": str, "replace": str, Optional("flags"): str},
    ),
    Optional("replace"): Any(
        ExactSequence([str, str]), {"search": str, "replace": str}
    ),
}

# Test case
case = Schema(
    {
        Optional("filters", default={}): filters,
        Any("equals", "regex", "contains"): Value,
        Optional("not"): [{Required(Any("equals", "regex", "contains")): Value}],
        Optional("expected", description="Expected value when used with regex"): Value,
    }
)

# Nested test cases
match = Any(
    All(Value, ToDict("equals"), ToList()),
    All(case, ToList()),
    [All(Value, lambda x: ToDict("equals")), case],
)


common = {
    Optional("name", default="", description="Test Name"): str,
    Optional("executable", default=None, description="Path to the executable"): Any(
        str, None
    ),
    Optional("env", default={}): {str: Value},
    Optional("tty", default=False): Boolean(),
    Optional("timeout", default=-1): Any(float, int),
    Optional(
        Exclusive(
            "points", "points_or_weight", description="Points given for this test"
        )
    ): Any(float, int),
    Optional(
        Exclusive("weight", "points_or_weight", description="Weight of the test")
    ): Any(float, int),
    Optional("min-points", default=0.1): Any(float, int),
}

test = Schema(
    {
        Optional("args", default=[]): [Value],
        Optional("stdin", default=""): Any(Value, None),
        Optional("stdout", default=[]): match,
        Optional("stderr", default=[]): match,
        Optional("exit"): Any(int, str, bool),
    }
).extend(common)

Num = TrackId()

group = Schema(
    {Required("tests"): All(Num.down(), [All(Any(Self, test), Num.next())], Num.up())}
).extend(common)

cli = {
    Optional("verbose"): Any(int),
    Optional("report"): str,
    Optional("format"): Any("json", "yaml"),
    Optional("table", default=False): Boolean(),
}


def SchemaConfig(data, humanize=False):  # noqa: N802
    """Validate the given data against the schema."""
    schema = (
        Schema(
            {
                Optional("name"): str,
                Optional("version", default=2): Any(1, 2),
                Optional("filters", default={}): filters,
                Required("tests"): All(
                    Num.reset(), [All(Any(test, group), Num.next())]
                ),
                Optional("points"): Any(float, int),
                Optional("min-points", default=0.1): Any(float, int),
            }
        )
        .extend(common)
        .extend(evaluate)
        .extend(cli)
    )
    if humanize:
        return validate_with_humanized_errors(data, schema)
    return schema(data)
