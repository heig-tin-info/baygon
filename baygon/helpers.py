import shlex


def escape_argument(arg):
    return shlex.quote(arg)


def create_command_line(args):
    escaped_args = [escape_argument(str(arg)) for arg in args]
    return " ".join(escaped_args)
