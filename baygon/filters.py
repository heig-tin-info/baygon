""" String filters for Baygon.
Each filter is a class that implements a filter method.
A filter is used to modify `stdout` and `stderr` before they are tested.
"""
import re
import sys
import inspect
from abc import ABC, abstractmethod
from collections.abc import Sequence
from tinykernel import TinyKernel
from .error import InvalidFilterError


class Filter(ABC):
    """ Base class for filters. """
    # Input filter, used to modify the input before it is sent to the program
    __input__ = False

    # Output filter, used to modify the output before it is tested
    __output__ = True

    @abstractmethod
    def filter(self, value: str) -> str:
        """ Return True if the value matches the filter. """
        return value

    def __init__(self, *args, **kwargs):
        ...

    def __repr__(self):
        return f'{self.__class__.__name__}'

    def __call__(self, value: str) -> str:
        return self.filter(value)

    @classmethod
    def name(cls):
        """ Return the name of the filter. """
        return cls.__name__.split('Filter', maxsplit=1)[1].lower()


class FilterNone(Filter):
    """ Filter that does nothing. """

    def filter(self, value: str) -> str:
        return value


class FilterUppercase(Filter):
    """ Filter for uppercase strings.
    >>> f = FilterUppercase()
    >>> f('hello')
    'HELLO'
    """
    __output__ = True

    def filter(self, value: str) -> str:
        return value.upper()


class FilterLowercase(Filter):
    """ Filter for lowercase strings.
    >>> f = FilterLowercase()
    >>> f('HELLO')
    'hello'
    """
    __output__ = True

    def filter(self, value: str) -> str:
        return value.lower()


class FilterTrim(Filter):
    """ Filter for trimmed strings.
    >>> f = FilterTrim()
    >>> f(' hello   ')
    'hello'
    """
    __output__ = True

    def filter(self, value: str) -> str:
        return value.strip()


class FilterIgnoreSpaces(Filter):
    """ Filter for strings with no spaces.
    >>> f = FilterIgnoreSpaces()
    >>> f('hello   world')
    'helloworld'
    """
    __output__ = True

    def filter(self, value: str) -> str:
        return value.replace(' ', '')


class FilterReplace(Filter):
    """ Filter for strings with simple replacements.
    >>> f = FilterReplace('hello', 'world')
    >>> f('hello world')
    'world world'
    """
    __output__ = True

    def __init__(self, pattern: str, replacement: str):
        super().__init__()
        self.pattern = pattern
        self.replacement = replacement

    def filter(self, value: str) -> str:
        return value.replace(self.pattern, self.replacement)


class FilterRegex(Filter):
    """ Filter for strings using regular expressions.
    >>> f = FilterRegex('[aeiou]', '-')
    >>> f('hello world')
    'h-ll- w-rld'
    """
    __output__ = True

    def __init__(self, pattern: str, replacement: str):
        super().__init__()
        self.pattern = pattern
        self.replacement = replacement
        self.regex = re.compile(pattern)

    def filter(self, value: str) -> str:
        return self.regex.sub(self.replacement, value)


class FilterEval(Filter):
    """ Filter for evaluating mustaches in strings.
    """
    __input__ = True

    def __init__(self, open: str = '{{', close: str = '}}', init: list = None):
        super().__init__()
        self._mustache = re.compile(f'{open}(.*?){close}')
        self._kernel = TinyKernel()

        init = init or [
            'from math import *',
            'from random import *',
            'from statistics import *',
            'from baygon.eval import iter',
        ]

        for item in init:
            self._kernel(item)

    def filter(self, value: str) -> str:
        """ Evaluate mustaches in a string. """
        pos = 0
        ret = ''
        for match in self._mustache.finditer(value):
            ret += value[pos:match.start()]
            ret += str(self.exec(match.group(1)))
            pos = match.end()
        return ret

    def exec(self, code: str):
        """ Execute code in the kernel. """

        # Inject context to custom functions
        code = re.sub(r'((?<=\b)iter\(.*?)(\))',
                      f'\\1,ctx={hash(code)}\\2', code)

        # Workaround to get the value of assignments
        try:
            self._kernel('_ = ' + code)
            return self._kernel.glb['_']
        except SyntaxError:
            return self._kernel(code)


class Filters(Filter, Sequence):
    """ A sequence of filters. """
    __input__ = True
    __output__ = True

    def __init__(self, filters=None):
        super().__init__()
        self._filters = self._parse_filter(filters)

    def _parse_filter(self, filters):

        if filters is None:
            return []
        if isinstance(filters, Filter):
            return [filters]
        if isinstance(filters, Filters):
            return filters._filters
        if isinstance(filters, dict):
            instances = []
            for name, args in filters.items():
                if not isinstance(args, list):
                    args = [args]
                instances.append(filter_map[name](*args))
            return instances

        raise InvalidFilterError(f'Invalid type for filters: {type(filters)}')

    def __getitem__(self, index):
        return self._filters[index]

    def __len__(self):
        return len(self._filters)

    def extend(self, filters):
        """ Extend the filters with another Filters object. """
        self._filters.extend(self._parse_filter(filters))
        return self

    def filter(self, value: str, input=True) -> str:
        for filter_ in self._filters:
            if (input and filter_.__input__) or (
                    not input and filter_.__output__):
                value = filter_.filter(value)
        return value

    def __repr__(self):
        return f'{self.__class__.__name__}<{self._filters}>'


def get_filters():
    filter_map = {}
    for name, cls in inspect.getmembers(sys.modules[__name__]):
        if not inspect.isclass(cls) or not name.startswith('Filter'):
            continue
        if len(cls.name()) < 2:
            continue
        filter_map[cls.name()] = cls
    return filter_map


filter_map = get_filters()
