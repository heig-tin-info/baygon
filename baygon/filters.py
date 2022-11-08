""" String filters for Baygon.
Each filter is a class that implements a filter method.
A filter is used to modify `stdout` and `stderr` before they are tested.
"""
import re
from abc import ABC, abstractmethod
from collections.abc import Sequence

from .error import InvalidFilterError


class Filter(ABC):
    """ Base class for filters. """
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
    type = 'uppercase'

    def filter(self, value: str) -> str:
        return value.upper()


class FilterLowercase(Filter):
    """ Filter for lowercase strings.
    >>> f = FilterLowercase()
    >>> f('HELLO')
    'hello'
    """

    type = 'lowercase'

    def filter(self, value: str) -> str:
        return value.lower()


class FilterTrim(Filter):
    """ Filter for trimmed strings.
    >>> f = FilterTrim()
    >>> f(' hello   ')
    'hello'
    """
    type = 'trim'

    def filter(self, value: str) -> str:
        return value.strip()


class FilterIgnoreSpaces(Filter):
    """ Filter for strings with no spaces.
    >>> f = FilterIgnoreSpaces()
    >>> f('hello   world')
    'helloworld'
    """
    type = 'ignorespaces'

    def filter(self, value: str) -> str:
        return value.replace(' ', '')


class FilterReplace(Filter):
    """ Filter for strings with simple replacements.
    >>> f = FilterReplace('hello', 'world')
    >>> f('hello world')
    'world world'
    """
    type = 'replace'

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
    type = 'regex'

    def __init__(self, pattern: str, replacement: str):
        super().__init__()
        self.pattern = pattern
        self.replacement = replacement
        self.regex = re.compile(pattern)

    def filter(self, value: str) -> str:
        return self.regex.sub(self.replacement, value)


class Filters(Filter, Sequence):
    """ A sequence of filters. """
    type = 'filters'

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

    def filter(self, value: str) -> str:
        for filter_ in self._filters:
            value = filter_.filter(value)
        return value

    def __repr__(self):
        return f'{self.__class__.__name__}<{self._filters}>'


filter_map = {
    'uppercase': FilterUppercase,
    'lowercase': FilterLowercase,
    'trim': FilterTrim,
    'ignorespaces': FilterIgnoreSpaces,
    'replace': FilterReplace,
    'regex': FilterRegex,
}
