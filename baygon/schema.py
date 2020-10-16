from voluptuous import Schema, ExactSequence, IsFile, Coerce, Required, Any, All, Number, Optional

match = Any(
    All(Number(), Coerce(str), lambda x: [{'equals': x}]),
    All(str, lambda x: [{'equals': x}]),
    [
        All(str, lambda x: {'equals': x}),
        {
            Optional('uppercase'): bool,
            Optional('lowercase'): bool,
            Optional('trim'): bool,
            Required(Any('equals', 'regex', 'contains')): str
        }
    ]
)

test = Schema({
    Optional('name'): str,
    Optional('args'): [Any(str, All(Number(), Coerce(str)))],
    Optional('stdin', default=None): Any(None, str, [str]),
    Optional('stdout', default=[]): match,
    Optional('stderr', default=[]): match,
    Optional('exit-status'): All(Any(int, bool), Coerce(int))
})

group = Schema({
    Optional('name', default=''): str,
    Required('tests'): [test]
})

schema = Schema({
    Required('version'): 1,
    Optional('name', default=''): str,
    Optional('executable'): IsFile('Missing configuration file'),
    Optional('filters'): {
        Optional('uppercase'): bool,
        Optional('lowercase'): bool,
        Optional('trim'): bool,
        Optional('regex'): ExactSequence([str, str])
    },
    Required('tests'): [Any(test, group)]
})
