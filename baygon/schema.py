""" YAML Schema for Baygon test files. """
from voluptuous import All, Any, Boolean, Coerce, ExactSequence, Optional, Required
from voluptuous import Schema as VSchema
from voluptuous import Self
from voluptuous.humanize import validate_with_humanized_errors

from .id import Id


class TrackId:
    """ Keep the id of the test. """

    def __init__(self):
        self._id = Id()

    def reset(self):
        """ Reset the id. """
        def _(v):
            self._id = Id()
            return v
        return _

    def down(self):
        """ Return a new Id with the given id appended. """
        def _(v):
            self._id = self._id.down()
            return v
        return _

    def up(self):
        """ Return a new Id with the given id appended. """
        def _(v):
            self._id = self._id.up()
            return v
        return _

    def next(self):
        """ Return a new Id with the last id incremented. """
        def _(v):
            v['test_id'] = list(self._id)
            self._id = self._id.next()
            return v
        return _


Value = Any(str,
            All(Any(int, float, All(bool, Coerce(int))), Coerce(str)))

# Global test filters
filters = {
    Optional('uppercase'): Boolean(),
    Optional('lowercase'): Boolean(),
    Optional('trim'): Boolean(),
    Optional(Any('ignorespaces', 'ignore-spaces')): Boolean(),
    Optional('regex'): ExactSequence([str, str]),
    Optional('replace'): ExactSequence([str, str]),
}

# Test case
case = {
    Optional('filters', default={}): filters,
    Any('equals', 'regex', 'contains'): Value,
    Optional('not'): [{Required(Any('equals', 'regex', 'contains')): Value}],
    Optional('expected',
             description="Expected value when used with regex"): Value,
}

# Nested test cases
match = Any(
    All(Value, lambda x: [{'equals': x}]),
    [
        All(Value, lambda x: {'equals': x}),
        case
    ],
    case,
)

common = {
    Optional('name',
             default='',
             description='Test Name'): str,
    Optional('executable',
             default=None,
             description='Path to the executable'): Any(str, None),
    Optional('points',
             default=0,
             description="Points given for this test"): int,
}

test = VSchema({
    Optional('args', default=[]): [Value],
    Optional('env', default={}): {str: Value},

    Optional('stdin', default=''): Any(Value, None),
    Optional('stdout', default=[]): match,
    Optional('stderr', default=[]): match,

    Optional('exit'): All(Any(int, Boolean()), Coerce(int))
}).extend(common)

Num = TrackId()

group = VSchema({
    Required('tests'): All(Num.down(),
                           [All(Any(Self, test), Num.next())],
                           Num.up())
}).extend(common)


def Schema(data, humanize=False):  # noqa: N802
    """ Validate the given data against the schema. """
    schema = VSchema({
        Optional('name'): str,
        Optional('version', default=2): Any(1, 2),
        Optional('filters', default={}): filters,
        Required('tests'): All(Num.reset(),
                               [All(Any(test, group), Num.next())])
    }).extend(common)
    if humanize:
        return validate_with_humanized_errors(data, schema)
    return schema(data)
