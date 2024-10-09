import inspect
import re
import sys
from abc import ABC, abstractmethod
from functools import lru_cache


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
        return f"{self.__class__.__name__}<{str(self)}>"


class InvalidExitStatus(InvalidCondition):
    """Invalid exit status error."""

    def __str__(self):
        return f"Invalid exit status: " f"{self.value} != {self.expected}."


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
        return f"Output {value} does not equal '{self.expected}' on " f"{self.on}."


class MatchBase(ABC):
    """Base class for all matchers."""

    def __init__(self, inverse=False, **kwargs):
        """Initialize the matcher."""
        self.inverse = inverse

    @classmethod
    def name(cls):
        """Return the name of the filter."""
        return cls.__name__.split("Match", maxsplit=1)[1].lower()

    @abstractmethod
    def __call__(self, value, **kwargs):
        """Match the value against the condition."""
        raise NotImplementedError


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

    @classmethod
    @lru_cache()
    def matchers(cls):
        """Helper to get all matchers by their name."""
        fmap = {}
        for _, member in inspect.getmembers(sys.modules[__name__]):
            if not inspect.isclass(member) or not hasattr(member, "name"):
                continue
            if member.name() == "base":
                continue
            fmap[member.name()] = member
        return fmap

    def __new__(cls, name, *args, **kwargs) -> MatchBase:
        if name not in cls.matchers():
            raise ValueError(f"Unknown matcher: {name}")
        return cls.matchers()[name](*args, **kwargs)
