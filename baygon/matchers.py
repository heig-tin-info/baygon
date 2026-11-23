"""Output matchers used to assert command results."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
import math
import re
from typing import TypeVar

MatchType = TypeVar("MatchType", bound="MatchBase")

#: Lines longer than this are cut around their first difference.
LINE_WIDTH = 72

#: Outputs quoted in a message are cut after this many characters.
PREVIEW_LENGTH = 200


def _show(line):
    """Quote a line, making tabs and carriage returns visible.

    >>> print(_show("a\\tb "))
    'a\\tb '
    """
    return "'" + line.replace("\t", "\\t").replace("\r", "\\r") + "'"


def _preview(text):
    """Cut a long output quoted in a message.

    >>> _preview("abc")
    'abc'
    >>> len(_preview("x" * 500))
    201
    """
    if len(text) <= PREVIEW_LENGTH:
        return text
    return text[:PREVIEW_LENGTH] + "…"


def _window(expected, found, width=LINE_WIDTH):
    """Cut two lines around their first difference, keeping them aligned.

    >>> _window("short", "shirt")
    ('short', 'shirt')
    >>> _window("a" * 100 + "X", "a" * 100 + "Y", width=10)
    ('…aaaaaaaaaX', '…aaaaaaaaaY')
    >>> _window("1 -> " * 30, "1", width=12)
    ('1 -> 1 -> 1 …', '1')
    """
    longest = max(len(expected), len(found))
    if longest <= width:
        return expected, found
    column = next(
        (i for i, (a, b) in enumerate(zip(expected, found, strict=False)) if a != b),
        min(len(expected), len(found)),
    )
    start = max(0, min(column - width // 3, longest - width))

    def _cut(line):
        part = line[start : start + width]
        if start > 0:
            part = "…" + part
        if start + width < len(line):
            part += "…"
        return part

    return _cut(expected), _cut(found)


def describe_difference(stream, expected, found):
    """Explain where an output first differs from the expected one.

    >>> print(describe_difference("stdout", "a\\nb\\n", "a\\nc\\n"))
    Output stdout differs from the expected output on line 2:
      expected: 'b'
      found:    'c'
    >>> print(describe_difference("stdout", "a\\nb\\n", "a\\n"))
    Output stdout differs from the expected output on line 2:
      expected: 'b'
      found:    (end of output)
    >>> print(describe_difference("stdout", "a\\n", ""))
    Output stdout differs from the expected output on line 1:
      expected: 'a'
      found:    (empty output)
    >>> print(describe_difference("stdout", "1 -> " * 20 + "\\n", ""))
    Output stdout differs from the expected output on line 1:
      expected: '1 -> 1 -> 1 -> 1 -> 1 -> 1 -> 1 -> 1 -> 1 -> 1 -> 1 -> 1 -> 1 -> 1 -> 1 …'
      found:    (empty output)
    >>> print(describe_difference("stdout", "a\\n", "a"))
    Output stdout has the expected lines, but the newline at the end is missing.
    """
    expected_lines = expected.splitlines()
    found_lines = found.splitlines()
    for index in range(max(len(expected_lines), len(found_lines))):
        want = expected_lines[index] if index < len(expected_lines) else None
        got = found_lines[index] if index < len(found_lines) else None
        if want != got:
            break
    else:
        if expected.endswith("\n") and not found.endswith("\n"):
            reason = "the newline at the end is missing"
        elif found.endswith("\n") and not expected.endswith("\n"):
            reason = "there is an extra newline at the end"
        else:
            reason = "the line endings differ"
        return f"Output {stream} has the expected lines, but {reason}."

    cut_want, cut_got = _window(want or "", got or "")
    want = None if want is None else cut_want
    got = None if got is None else cut_got
    shown_want = "(end of output)" if want is None else _show(want)
    if got is not None:
        shown_got = _show(got)
    else:
        shown_got = "(empty output)" if not found else "(end of output)"
    return (
        f"Output {stream} differs from the expected output on line {index + 1}:\n"
        f"  expected: {shown_want}\n"
        f"  found:    {shown_got}"
    )


class InvalidCondition:
    """Invalid test case condition.

    ``message`` is the explanation written by the author of the test, shown
    with the issue when it is set.
    """

    message = None

    def __init__(self, value, expected, on=None, test=None, inverse=False, **kwargs):
        self.on = on
        self.test = test
        self.value = value
        self.expected = expected
        self.inverse = inverse

    def __str__(self):
        return (
            f'Expected value "{self.expected}" on {self.on}, '
            f'but got "{self.value}" instead.'
        )

    def __repr__(self):
        return f"{self.__class__.__name__}<{self!s}>"


class InvalidExitStatus(InvalidCondition):
    """Invalid exit status error.

    ``value`` is the expected status and ``expected`` the actual one, the order
    used since the first versions.

    >>> str(InvalidExitStatus(0, 1))
    'Invalid exit status: expected 0, got 1.'
    """

    def __str__(self):
        return f"Invalid exit status: expected {self.value}, got {self.expected}."


class ExecutionTimeout(InvalidCondition):
    """The program was killed after its time limit.

    >>> str(ExecutionTimeout(None, 1.5))
    'Timeout after 1.5 s.'
    """

    def __init__(self, value, expected, **kwargs):
        super().__init__(value, expected, **kwargs)
        self.on = self.on or "exit"

    def __str__(self):
        return f"Timeout after {self.expected:g} s."


class OutputLimitExceeded(InvalidCondition):
    """An output stream went over the size limit, the program was killed.

    >>> str(OutputLimitExceeded(None, 1024))
    'Output limit exceeded (more than 1024 bytes), the program was killed.'
    """

    def __str__(self):
        return (
            f"Output limit exceeded (more than {self.expected} bytes), "
            "the program was killed."
        )


class ExecutionFailed(InvalidCondition):
    """The program could not be started."""

    def __str__(self):
        return f"Unable to execute {self.expected}: {self.value}"


class InvalidTestDefinition(InvalidCondition):
    """The test could not be evaluated (invalid regex, eval error...).

    >>> str(InvalidTestDefinition(ValueError("bad"), None))
    'Invalid test: ValueError: bad'
    """

    def __str__(self):
        return f"Invalid test: {type(self.value).__name__}: {self.value}"


class InvalidNumber(InvalidCondition):
    """The output is not the expected number.

    ``value`` is the output, ``expected`` describes the expectation.
    """

    def __str__(self):
        text = self.value.strip()
        if self.inverse:
            return f"Output {self.on} is {text}, it should not be {self.expected}."
        if _parse_number(text) is None:
            shown = text if len(text) <= 60 else text[:57] + "..."
            return (
                f'Output {self.on} is not a number: "{shown}" '
                f"(expected {self.expected})."
            )
        return f"Output {self.on} is {text}, expected {self.expected}."


class InvalidCount(InvalidCondition):
    """The output does not have the expected number of characters or lines.

    >>> str(InvalidCount(4, "at most 3", unit="lines", on="stdout"))
    'Output stdout has 4 lines, expected at most 3.'
    """

    def __init__(self, value, expected, unit="characters", **kwargs):
        super().__init__(value, expected, **kwargs)
        self.unit = unit

    def __str__(self):
        if self.inverse:
            return (
                f"Output {self.on} has {self.value} {self.unit}, "
                f"it should not have {self.expected}."
            )
        return (
            f"Output {self.on} has {self.value} {self.unit}, expected {self.expected}."
        )


class InvalidSameAs(InvalidCondition):
    """The output differs from the output of the reference program.

    >>> str(InvalidSameAs("1", "2", reference="./ref", on="stdout"))
    "Output stdout '1' differs from the reference ./ref: '2'."
    """

    def __init__(self, value, expected, reference=None, **kwargs):
        super().__init__(value, expected, **kwargs)
        self.reference = reference

    def __str__(self):
        value = "(empty)" if not self.value else f"'{self.value}'"
        expected = "(empty)" if not self.expected else f"'{self.expected}'"
        return (
            f"Output {self.on} {value} differs from the reference "
            f"{self.reference}: {expected}."
        )


class HelperProgramFailed(InvalidCondition):
    """A generator or reference program used by the test failed.

    >>> str(HelperProgramFailed("exit status 1", "Generator ./gen"))
    'Generator ./gen failed: exit status 1.'
    """

    def __str__(self):
        return f"{self.expected} failed: {str(self.value).rstrip('.!')}."


class InvalidContains(InvalidCondition):
    """Invalid contains error."""

    def __str__(self):
        if self.inverse:
            return (
                f"Output {self.on} should not contain {self.expected}. "
                f'Found "{_preview(self.value)}".'
            )
        return (
            f"Output {self.on} does not contain {self.expected}. "
            f'Found "{_preview(self.value)}" instead.'
        )


class InvalidRegex(InvalidCondition):
    """Invalid regex error."""

    def __str__(self):
        value = _preview(self.value)
        if self.inverse:
            return (
                f"Output '{self.on}' should not match /{self.expected}/ on \"{value}\"."
            )
        return f"Output '{self.on}' does not match /{self.expected}/ on \"{value}\"."


class InvalidEquals(InvalidCondition):
    """Invalid equals error.

    Short one-line outputs are quoted whole, longer ones are described by
    their first differing line.

    >>> str(InvalidEquals("4", "3", on="stdout"))
    "Output '4' does not equal '3' on stdout."
    >>> print(InvalidEquals("1\\n", "1 (0 steps)\\n", on="stdout"))
    Output stdout differs from the expected output on line 1:
      expected: '1 (0 steps)'
      found:    '1'
    """

    def __str__(self):
        value = "(empty)" if not self.value else f"'{_preview(self.value)}'"
        if self.inverse:
            return (
                f"Output {value} should not equal '{_preview(self.expected)}' "
                f"on {self.on}."
            )
        if _is_short(self.value) and _is_short(self.expected):
            return f"Output {value} does not equal '{self.expected}' on {self.on}."
        return describe_difference(self.on, self.expected, self.value)


def _is_short(text):
    """A short text holds on one line and is quoted whole in messages."""
    return "\n" not in text and len(text) <= LINE_WIDTH // 2


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
            return InvalidRegex(
                value, self.pattern.pattern, inverse=self.inverse, **kwargs
            )
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
            return InvalidContains(value, self.contains, inverse=self.inverse, **kwargs)
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
            return InvalidEquals(value, self.equal, inverse=self.inverse, **kwargs)
        return None


def _parse_number(text):
    """Return the number written in ``text``, or None.

    >>> _parse_number(" 12.5 ")
    12.5
    >>> _parse_number("12 apples") is None
    True
    """
    try:
        number = float(text.strip())
    except (TypeError, ValueError):
        return None
    return None if math.isnan(number) else number


def _to_number(value, name):
    if value is None:
        return None
    number = _parse_number(str(value))
    if number is None:
        raise ValueError(f"{name} must be a number, got '{value}'")
    return number


def _fmt(number):
    return str(int(number)) if float(number).is_integer() else repr(float(number))


class _RangeMatch(MatchBase):
    """Base of the matchers comparing a measure to a value or a range."""

    def __init__(self, spec, **kwargs):
        """Initialize the matcher from ``{value}`` or ``{min, max}``."""
        spec = dict(spec) if isinstance(spec, dict) or hasattr(spec, "items") else {}
        self.value = _to_number(spec.get("value"), "value")
        self.min = _to_number(spec.get("min"), "min")
        self.max = _to_number(spec.get("max"), "max")
        super().__init__(**kwargs)

    def _in_range(self, measure):
        if self.min is not None and measure < self.min:
            return False
        return not (self.max is not None and measure > self.max)

    def _describe_range(self):
        if self.min is not None and self.max is not None:
            return f"between {_fmt(self.min)} and {_fmt(self.max)}"
        if self.min is not None:
            return f"at least {_fmt(self.min)}"
        return f"at most {_fmt(self.max)}"


@register_matcher
class MatchNumber(_RangeMatch):
    """Match if the output is a number equal to a value or within a range.

    >>> MatchNumber({"value": 3.14, "tolerance": 0.01})(" 3.1416\\n") is None
    True
    >>> str(MatchNumber({"min": 0})("-1", on="stdout"))
    'Output stdout is -1, expected at least 0.'
    """

    def __init__(self, spec, **kwargs):
        """Initialize the matcher."""
        super().__init__(spec, **kwargs)
        spec = dict(spec)
        self.tolerance = _to_number(spec.get("tolerance"), "tolerance")

    def describe(self):
        """Describe the expected number."""
        if self.value is None:
            return self._describe_range()
        if self.tolerance:
            return f"{_fmt(self.value)} ± {_fmt(self.tolerance)}"
        return _fmt(self.value)

    def _matches(self, number):
        if number is None:
            return False
        if self.value is None:
            return self._in_range(number)
        tolerance = 1e-9 if self.tolerance is None else self.tolerance
        return math.isclose(number, self.value, rel_tol=1e-9, abs_tol=tolerance)

    def __call__(self, value, **kwargs):
        if (not self._matches(_parse_number(value))) ^ self.inverse:
            return InvalidNumber(value, self.describe(), inverse=self.inverse, **kwargs)
        return None


class _CountMatch(_RangeMatch):
    unit = "characters"

    @abstractmethod
    def measure(self, value):
        """Return the measured quantity of the output."""

    def describe(self):
        """Describe the expected count."""
        if self.value is not None:
            return f"exactly {_fmt(self.value)}"
        return self._describe_range()

    def __call__(self, value, **kwargs):
        measure = self.measure(value)
        if self.value is not None:
            ok = measure == self.value
        else:
            ok = self._in_range(measure)
        if (not ok) ^ self.inverse:
            return InvalidCount(
                measure, self.describe(), unit=self.unit, inverse=self.inverse, **kwargs
            )
        return None


@register_matcher
class MatchLength(_CountMatch):
    """Match the number of characters of the output.

    >>> MatchLength({"max": 5})("hello") is None
    True
    """

    unit = "characters"

    def measure(self, value):
        """Return the number of characters."""
        return len(value)


@register_matcher
class MatchLines(_CountMatch):
    """Match the number of lines of the output.

    >>> str(MatchLines({"value": 2})("a\\nb\\nc\\n", on="stdout"))
    'Output stdout has 3 lines, expected exactly 2.'
    """

    unit = "lines"

    def measure(self, value):
        """Return the number of lines."""
        return len(value.splitlines())


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
