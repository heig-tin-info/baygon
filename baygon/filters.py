"""String filters for Baygon.
Each filter is a class that implements a filter method.
A filter is used to modify `stdout` and `stderr` before they are tested.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
import re
from typing import Callable, TypeVar

from tinykernel import TinyKernel

from .error import InvalidFilterError


FilterType = TypeVar("FilterType", bound="Filter")


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

        Args:
            *args: Positional arguments forwarded by subclasses.
            **kwargs: Keyword arguments, notably `input` to mark filters for stdin.
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


_FILTER_REGISTRY: dict[str, type[Filter]] = {}


def register_filter(
    name: str | None = None,
) -> Callable[[type[FilterType]], type[FilterType]] | type[FilterType]:
    """Register a filter so it can be referenced from configuration.

    Usage examples:

    >>> @register_filter
    ... class FilterFoo(Filter):
    ...     ...
    >>>
    >>> @register_filter("bar")
    ... class CustomFilter(Filter):
    ...     ...
    """

    def decorator(cls: type[FilterType]) -> type[FilterType]:
        key = (name or cls.name()).lower()
        existing = _FILTER_REGISTRY.get(key)
        if existing is not None and existing is not cls:
            raise ValueError(f"Filter '{key}' is already registered.")
        _FILTER_REGISTRY[key] = cls
        return cls

    if isinstance(name, type):
        cls = name
        name = None
        return decorator(cls)
    return decorator


def get_registered_filters() -> dict[str, type[Filter]]:
    """Return a copy of the registered filters mapping."""
    return dict(_FILTER_REGISTRY)


@register_filter
class FilterNone(Filter):
    """Filter that does nothing."""

    def apply(self, value: str) -> str:
        return value


@register_filter
class FilterUppercase(Filter):
    """Filter for uppercase strings.
    >>> f = FilterUppercase()
    >>> f("hello")
    'HELLO'
    """

    def apply(self, value: str) -> str:
        return value.upper()


@register_filter
class FilterLowercase(Filter):
    """Filter for lowercase strings.
    >>> f = FilterLowercase()
    >>> f("HELLO")
    'hello'
    """

    def apply(self, value: str) -> str:
        return value.lower()


@register_filter
class FilterTrim(Filter):
    """Filter for trimmed strings.
    >>> f = FilterTrim()
    >>> f(" hello   ")
    'hello'
    """

    __output__ = True

    def apply(self, value: str) -> str:
        return value.strip()


@register_filter
class FilterIgnoreSpaces(Filter):
    """Filter for strings with no spaces.
    >>> f = FilterIgnoreSpaces()
    >>> f("hello   world")
    'helloworld'
    """

    def apply(self, value: str) -> str:
        return value.replace(" ", "")


@register_filter
class FilterReplace(Filter):
    """Filter for strings with simple replacements.
    >>> f = FilterReplace("hello", "world")
    >>> f("hello world")
    'world world'
    """

    def __init__(self, pattern: str, replacement: str):
        super().__init__()
        self.pattern = pattern
        self.replacement = replacement

    def apply(self, value: str) -> str:
        return value.replace(self.pattern, self.replacement)


@register_filter
class FilterRegex(Filter):
    """Filter for strings using regular expressions.
    >>> f = FilterRegex("[aeiou]", "-")
    >>> f("hello world")
    'h-ll- w-rld'
    """

    def __init__(self, pattern: str, replacement: str):
        super().__init__()
        self.pattern = pattern
        self.replacement = replacement
        self.regex = re.compile(pattern)

    def apply(self, value: str) -> str:
        return self.regex.sub(self.replacement, value)


@register_filter
class FilterEval(Filter):
    """Filter for evaluating mustaches in strings."""

    def __init__(
        self, start: str = "{{", end: str = "}}", init: list[str] | None = None
    ):
        super().__init__()
        self._mustache = re.compile(f"{start}(.*?){end}")
        self._kernel = TinyKernel()

        seed = list(init) if init is not None else []
        seed += [
            "from math import *",
            "from random import *",
            "from statistics import *",
            "from baygon.eval import iter",
        ]

        for item in seed:
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
            return list(filters)
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

    @staticmethod
    def _get_filter_class(name: str) -> type[Filter]:
        key = name.lower()
        try:
            return _FILTER_REGISTRY[key]
        except KeyError as exc:
            raise ValueError(f"Unknown filter: {name}") from exc

    def __new__(cls, name, *args, **kwargs) -> Filter:
        filter_cls = cls._get_filter_class(name)
        return filter_cls(*args, **kwargs)
