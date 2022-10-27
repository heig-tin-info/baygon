""" YAML Schema for Baygon test files. """
from voluptuous import (Schema, ExactSequence,
                        Coerce, Required,
                        Any, All, Optional)

value = Any(str, All(Any(int, float), Coerce(str)))

# Global test filters
filters = {
    Optional('uppercase'): bool,
    Optional('lowercase'): bool,
    Optional('trim'): bool,
    Optional(Any('ignorespaces', 'ignore-spaces')): bool,
    Optional('regex'): ExactSequence([str, str]),
    Optional('replace'): ExactSequence([str, str]),
}

# Test case
case = {
    Optional('filters', default={}): filters,
    Any('equals', 'regex', 'contains'): value,
    Optional('not'): [{Required(Any('equals', 'regex', 'contains')): value}],
    Optional('expected',
             description="Expected value when used with regex"): value,
}

# Nested test cases
match = Any(
    All(value, lambda x: [{'equals': x}]),
    [
        All(value, lambda x: {'equals': x}),
        case
    ],
    case,
)

common = {
    Optional('name', default=''): str,
    Optional('executable', default=None): Any(str, None),
}

# Test Suite
test_suite = Schema({**common, **{
    Optional('args', default=[]): [value],
    Optional('stdin', default=None): Any(value, None),
    Optional('stdout', default=[]): match,
    Optional('stderr', default=[]): match,
    Optional('env', default={}): {str: value},
    Optional('exit'): All(Any(int, bool), Coerce(int))
}})

subgroup = Schema({**common, **{
    Required('tests'): [test_suite]
}})

group = Schema({**common, **{
    Required('tests'): [Any(subgroup, test_suite)]
}})

schema = Schema({**common, **{
    Optional('version', default=1): 1,
    Optional('filters', default={}): filters,
    Required('tests'): [Any(test_suite, group)]
}})
