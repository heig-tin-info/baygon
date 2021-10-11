from voluptuous import (Schema, ExactSequence,
                        Coerce, Required,
                        Any, All, Optional)

value = Any(str, All(Any(int, float), Coerce(str)))

case = {
    'uppercase': bool,
    'lowercase': bool,
    'trim': bool,
    'ignorespaces': bool,
    Any('equals', 'regex', 'contains'): value,
    Optional('not'): [{Required(Any('equals', 'regex', 'contains')): value}],
    Optional('expected', description="Expected value when used with regex"): value,
}

match = Any(
    All(value, lambda x: [{'equals': x}]),
    [
        All(value, lambda x: {'equals': x}),
        case
    ],
    case,
)

test = Schema({
    Optional('name', default=''): str,
    Optional('args', default=[]): [value],
    Optional('stdin', default=None): Any(value, None),
    Optional('stdout', default=[]): match,
    Optional('stderr', default=[]): match,
    Optional('exit'): All(Any(int, bool), Coerce(int))
})

subgroup = Schema({
    Optional('name', default=''): str,
    Optional('executable', default=None): Any(str, None),
    Required('tests'): [test]
})

group = Schema({
    Optional('name', default=''): str,
    Optional('executable', default=None): Any(str, None),
    Required('tests'): [Any(subgroup, test)]
})

filters = Schema({
    Optional('uppercase'): bool,
    Optional('lowercase'): bool,
    Optional('trim'): bool,
    Optional('ignorespaces'): bool,
    Optional('regex'): ExactSequence([str, str])
})

schema = Schema({
    Optional('version', default=1): 1,
    Optional('name', default=''): str,
    Optional('executable', default=None): Any(str, None),
    Optional('filters', default={}): filters,
    Required('tests'): [Any(test, group)]
})
