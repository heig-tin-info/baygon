import re
import shlex


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
