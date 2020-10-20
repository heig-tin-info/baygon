from voluptuous import (Schema, ExactSequence, IsFile,
                        Coerce, Required,
                        Any, All, Number, Optional)

match = Any(
    All(Number(), Coerce(str), lambda x: [{'equals': x}]),
    All(str, lambda x: [{'equals': x}]),
    [
        All(str, lambda x: {'equals': x}),
        {
            Optional('uppercase'): bool,
            Optional('lowercase'): bool,
            Optional('trim'): bool,
            Required(Any('equals', 'regex', 'contains')): str,

            Optional('expected', description="Expected value when used with regex"): str,
        }
    ]
)

test = Schema({
    Optional('name', default=''): str,
    Optional('args', default=[]): [Any(str, All(Number(), Coerce(str)))],
    Optional('stdin', default=None): Any(None, str, [str]),
    Optional('stdout', default=[]): match,
    Optional('stderr', default=[]): match,
    Optional('exit'): All(Any(int, bool), Coerce(int))
})

group = Schema({
    Optional('name', default=''): str,
    Required('tests'): [test]
})

filters = Schema({
    Optional('uppercase'): bool,
    Optional('lowercase'): bool,
    Optional('trim'): bool,
    Optional('regex'): ExactSequence([str, str])
})

schema = Schema({
    Optional('version', default=1): 1,
    Optional('name', default=''): str,
    Optional('executable', default=None): Any(IsFile('Missing configuration file'), None),
    Optional('filters', default={}): filters,
    Required('tests'): [Any(test, group)]
})
