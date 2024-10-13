import re
import shlex
from pathlib import Path

from .error import ConfigError
from .schema import Schema


def escape_argument(arg):
    """Escape a command line argument.

    >>> print(escape_argument("hello"))
    hello
    >>> print(escape_argument("hello world"))
    'hello world'
    >>> print(escape_argument("hello'world'"))
    'hello'"'"'world'"'"''
    """
    return shlex.quote(arg)


def create_command_line(args):
    """Create a command line from a list of arguments.

    >>> print(create_command_line(["echo", "hello world"]))
    echo 'hello world'
    """
    escaped_args = [escape_argument(str(arg)) for arg in args]
    return " ".join(escaped_args)


class GreppableString(str):
    """A string that can be parsed with regular expressions."""

    def grep(self, pattern: str, *args) -> bool:
        """Return True if the pattern is found in the string.

        >>> GreppableString("hello world").grep("w.{3}d")
        ['world']
        >>> GreppableString("hello world").grep(r"\b[a-z]{4}\b")
        []
        """
        return re.findall(pattern, self, *args)

    def contains(self, value: str) -> bool:
        """Return True if the value is found in the string.

        >>> GreppableString("hello world").contains("world")
        True
        >>> GreppableString("hello world").contains("earth")
        False
        """
        return value in self


def find_testfile(path=None):
    """Recursively find the tests description file."""
    if not path:
        path = Path(".")
    elif isinstance(path, str):
        path = Path(path)

    path = path.resolve(strict=True)

    if path.is_file():
        return path

    for filename in ["baygon", "t", "test", "tests"]:
        for ext in ["json", "yml", "yaml"]:
            f = path.joinpath(f"{filename}.{ext}")
            if f.exists():
                return f

    # Recursively search in parent directories
    if path.parent == path:  # Test if root directory
        return None

    return find_testfile(path.parent)


def load_config(path=None):
    """Load a configuration file (can be YAML or JSON)."""
    path = find_testfile(path)

    if not path.exists():
        raise ConfigError(f"Couldn't find and configuration file in '{path.resolve()}'")

    return Schema(filename=path)
