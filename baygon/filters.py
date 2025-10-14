"""String filters for Baygon.
Each filter is a class that implements a filter method.
A filter is used to modify `stdout` and `stderr` before they are tested.
"""

import inspect
import re
import sys
from abc import ABC, abstractmethod
from collections.abc import Sequence
from functools import lru_cache

from tinykernel import TinyKernel

from .error import InvalidFilterError


class Filter(ABC):
    """Base class for filters."""

    @abstractmethod
    def apply(self, value: str) -> str:
        """Apply the filter to a value."""
        return value

    def filter(self, value: str) -> str:
        """Apply the filter to a value."""
        return self.apply(value)

    def __init__(self, *args, **kwargs):
        """Initialize the filter.
        Keyword arguments:

        input: Boolean Is the filter applied to the input?
        """
        self.input = kwargs.get("input", False)

    def __repr__(self):
        return f"{self.__class__.__name__}"

    def __call__(self, value: str) -> str:
        return self.filter(value)

    @classmethod
    def name(cls):
        """Return the name of the filter."""
        return cls.__name__.split("Filter", maxsplit=1)[1].lower()


class FilterNone(Filter):
    """Filter that does nothing."""

    def apply(self, value: str) -> str:
        return value


class FilterUppercase(Filter):
    """Filter for uppercase strings.
    >>> f = FilterUppercase()
    >>> f('hello')
    'HELLO'
    """

    def apply(self, value: str) -> str:
        return value.upper()


class FilterLowercase(Filter):
    """Filter for lowercase strings.
    >>> f = FilterLowercase()
    >>> f('HELLO')
    'hello'
    """

    def apply(self, value: str) -> str:
        return value.lower()


class FilterTrim(Filter):
    """Filter for trimmed strings.
    >>> f = FilterTrim()
    >>> f(' hello   ')
    'hello'
    """

    __output__ = True

    def apply(self, value: str) -> str:
        return value.strip()


class FilterIgnoreSpaces(Filter):
    """Filter for strings with no spaces.
    >>> f = FilterIgnoreSpaces()
    >>> f('hello   world')
    'helloworld'
    """

    def apply(self, value: str) -> str:
        return value.replace(" ", "")


class FilterReplace(Filter):
    """Filter for strings with simple replacements.
    >>> f = FilterReplace('hello', 'world')
    >>> f('hello world')
    'world world'
    """

    def __init__(self, pattern: str, replacement: str):
        super().__init__()
        self.pattern = pattern
        self.replacement = replacement

    def apply(self, value: str) -> str:
        return value.replace(self.pattern, self.replacement)


class FilterRegex(Filter):
    """Filter for strings using regular expressions.
    >>> f = FilterRegex('[aeiou]', '-')
    >>> f('hello world')
    'h-ll- w-rld'
    """

    def __init__(self, pattern: str, replacement: str):
        super().__init__()
        self.pattern = pattern
        self.replacement = replacement
        self.regex = re.compile(pattern)

    def apply(self, value: str) -> str:
        return self.regex.sub(self.replacement, value)


class FilterEval(Filter):
    """Filter for evaluating mustaches in strings."""

    def __init__(self, start: str = "{{", end: str = "}}", init: list = None):
        super().__init__()
        self._mustache = re.compile(f"{start}(.*?){end}")
        self._kernel = TinyKernel()

        init += [
            "from math import *",
            "from random import *",
            "from statistics import *",
            "from baygon.eval import iter",
        ]

        for item in init:
            self._kernel(item)

    def apply(self, value: str) -> str:
        """Evaluate mustaches in a string."""
        pos = 0
        ret = ""
        for match in self._mustache.finditer(value):
            ret += value[pos : match.start()]
            ret += str(self.exec(match.group(1)))
            pos = match.end()
        ret += value[pos:]
        return ret

    def exec(self, code: str):
        """Execute code in the kernel."""

        # Inject context to custom functions
        code = re.sub(r"((?<=\b)iter\(.*?)(\))", f"\\1,ctx={hash(code)}\\2", code)

        # Workaround to get the value of assignments
        try:
            self._kernel("_ = " + code)
            return self._kernel.glb["_"]
        except SyntaxError:
            return self._kernel(code)

    def __repr__(self):
        return f"{self.__class__.__name__}({self._mustache.pattern})"


class Filters(Filter, Sequence):
    """A sequence of filters."""

    def __init__(self, filters=None):
        super().__init__()
        self._filters = self._parse_filter(filters)

    def _parse_filter(self, filters):

        if filters is None:
            return []
        if isinstance(filters, Filter):
            return [filters]
        if isinstance(filters, Filters):
            return list(filters._filters)
        if isinstance(filters, dict):
            instances = []
            for name, args in filters.items():
                if not isinstance(args, list):
                    args = [args]
                instances.append(FilterFactory(name, *args))
            return instances

        raise InvalidFilterError(f"Invalid type for filters: {type(filters)}")

    def __getitem__(self, index):
        return self._filters[index]

    def __len__(self):
        return len(self._filters)

    def extend(self, filters):
        """Extend the filters with another Filters object."""
        self._filters.extend(self._parse_filter(filters))
        return self

    def apply(self, value: str) -> str:
        for filter_ in self._filters:
            value = filter_.filter(value)
        return value

    def __repr__(self):
        return f"{self.__class__.__name__}<{self._filters}>"


class FilterFactory:
    """Factory for filters."""

    @classmethod
    @lru_cache()
    def filters(cls):
        """Helper to get all filters by their name."""
        fmap = {}
        for _, member in inspect.getmembers(sys.modules[__name__]):
            if not inspect.isclass(member) or not hasattr(member, "name"):
                continue
            if member.name() == "base" or len(member.name()) < 2:
                continue
            fmap[member.name()] = member
        return fmap

    def __new__(cls, name, *args, **kwargs) -> Filter:
        if name not in cls.filters():
            raise ValueError(f"Unknown matcher: {name}")
        return cls.filters()[name](*args, **kwargs)
