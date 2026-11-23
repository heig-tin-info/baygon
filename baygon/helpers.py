import os
from pathlib import Path
import re
import shlex

from .i18n import tr


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


#: Lines of standard input shown with a command, the rest is summarized.
STDIN_LINES = 10


def display_program(path, start=None):
    """Write the path of a program as a student would type it.

    An absolute path is made relative to ``start`` (the current directory by
    default); a name looked up in the PATH is kept as is.

    >>> display_program("/home/me/lab/collatz", start="/home/me/lab")
    './collatz'
    >>> display_program("/home/me/lab/build/a.out", start="/home/me/lab")
    './build/a.out'
    >>> display_program("/home/me/other/prog", start="/home/me/lab")
    '../other/prog'
    >>> display_program("grep")
    'grep'
    """
    path = str(path)
    if not Path(path).is_absolute():
        return path
    try:
        relative = os.path.relpath(path, start)
    except ValueError:  # Another drive on Windows.
        return path
    if relative.startswith(os.pardir):
        return relative
    return os.curdir + os.sep + relative


def display_command(argv, stdin=None, start=None):
    """Lines of a shell session that run the command again.

    >>> display_command(["/lab/collatz", "abc", ""], start="/lab")
    ["$ ./collatz abc ''"]
    >>> display_command(["/lab/add"], stdin="1 2\\n", start="/lab")
    ["$ echo '1 2' | ./add"]
    >>> display_command(["/lab/add"], stdin="1 2", start="/lab")
    ["$ printf '%s' '1 2' | ./add"]
    >>> display_command(["/lab/add"], stdin="1\\n2\\n", start="/lab")
    ["$ ./add <<'EOF'", '1', '2', 'EOF']
    """
    if not argv:
        return []
    line = create_command_line([display_program(argv[0], start), *argv[1:]])
    if not stdin:
        return [f"$ {line}"]
    text = stdin[:-1] if stdin.endswith("\n") else stdin
    if "\n" not in text:
        if stdin.endswith("\n"):
            return [f"$ echo {escape_argument(text)} | {line}"]
        return [f"$ printf '%s' {escape_argument(text)} | {line}"]
    body = text.split("\n")
    if len(body) > STDIN_LINES:
        hidden = len(body) - STDIN_LINES
        body = [*body[:STDIN_LINES], tr("... ({count} more lines)", count=hidden)]
    return [f"$ {line} <<'EOF'", *body, "EOF"]


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
