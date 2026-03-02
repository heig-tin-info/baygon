"""Output matchers used to assert command results."""

from __future__ import annotations

from abc import ABC, abstractmethod
import re
from typing import Callable, TypeVar

MatchType = TypeVar("MatchType", bound="MatchBase")


class InvalidCondition:
    """Invalid test case condition."""

    def __init__(self, value, expected, on=None, test=None, **kwargs):
        self.on = on
        self.test = test
        self.value = value
        self.expected = expected

    def __str__(self):
        return (
            f'Expected value "{self.expected}" on {self.on}, '
            f'but got "{self.value}" instead.'
        )

    def __repr__(self):
        return f"{self.__class__.__name__}<{self!s}>"


class InvalidExitStatus(InvalidCondition):
    """Invalid exit status error."""

    def __str__(self):
        return f"Invalid exit status: {self.value} != {self.expected}."


class InvalidContains(InvalidCondition):
    """Invalid contains error."""

    def __str__(self):
        return (
            f"Output {self.on} does not contain {self.expected}. "
            f'Found "{self.value}" instead.'
        )


class InvalidRegex(InvalidCondition):
    """Invalid regex error."""

    def __str__(self):
        return (
            f"Output '{self.on}' does not match /{self.expected}/ "
            f'on "{self.value}".'
        )


class InvalidEquals(InvalidCondition):
    """Invalid equals error."""

    def __str__(self):
        value = "(empty)" if not self.value else f"'{self.value}'"
        return f"Output {value} does not equal '{self.expected}' on {self.on}."


class MatchBase(ABC):
    """Base class for all matchers."""

    def __init__(self, inverse=False, **kwargs):
        """Initialize the matcher."""
        self.inverse = inverse

    @classmethod
    def name(cls):
        """Return the registration name of the matcher."""
        return cls.__name__.split("Match", maxsplit=1)[1].lower()

    @abstractmethod
    def __call__(self, value, **kwargs):
        """Match the value against the condition."""
        raise NotImplementedError


_MATCHER_REGISTRY: dict[str, type[MatchBase]] = {}


def register_matcher(
    name: str | None = None,
) -> Callable[[type[MatchType]], type[MatchType]] | type[MatchType]:
    """Register a matcher class that can be referenced from configuration."""

    def decorator(cls: type[MatchType]) -> type[MatchType]:
        key = (name or cls.name()).lower()
        existing = _MATCHER_REGISTRY.get(key)
        if existing is not None and existing is not cls:
            raise ValueError(f"Matcher '{key}' is already registered.")
        _MATCHER_REGISTRY[key] = cls
        return cls

    if isinstance(name, type):
        cls = name
        name = None
        return decorator(cls)
    return decorator


def get_registered_matchers() -> dict[str, type[MatchBase]]:
    """Return the registered matchers mapping."""
    return dict(_MATCHER_REGISTRY)


@register_matcher
class MatchRegex(MatchBase):
    """Match a regex."""

    def __init__(self, pattern, **kwargs):
        """Initialize the matcher."""
        self.pattern = re.compile(pattern)
        super().__init__(**kwargs)

    def __call__(self, value, **kwargs):
        if (not self.pattern.findall(value)) ^ self.inverse:
            return InvalidRegex(value, self.pattern.pattern, **kwargs)
        return None


@register_matcher
class MatchContains(MatchBase):
    """Match if a string contains a specific value."""

    def __init__(self, contains, **kwargs):
        """Initialize the matcher."""
        self.contains = contains
        super().__init__(**kwargs)

    def __call__(self, value, **kwargs):
        if (self.contains not in value) ^ self.inverse:
            return InvalidContains(value, self.contains, **kwargs)
        return None


@register_matcher
class MatchEquals(MatchBase):
    """Match if a string contains a specific value."""

    def __init__(self, equal, **kwargs):
        """Initialize the matcher."""
        self.equal = equal
        super().__init__(**kwargs)

    def __call__(self, value, **kwargs):
        if (self.equal != value) ^ self.inverse:
            return InvalidEquals(value, self.equal, **kwargs)
        return None


class MatcherFactory:
    """Factory for matchers."""

    @staticmethod
    def _get_matcher_class(name: str) -> type[MatchBase]:
        key = name.lower()
        try:
            return _MATCHER_REGISTRY[key]
        except KeyError as exc:
            raise ValueError(f"Unknown matcher: {name}") from exc

    def __new__(cls, name, *args, **kwargs) -> MatchBase:
        matcher_cls = cls._get_matcher_class(name)
        return matcher_cls(*args, **kwargs)
