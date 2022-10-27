""" Executable class. To be used with the Test class. """
import os
import re
import shutil
import typing
import subprocess
from collections import namedtuple
from .filter import apply_filters

Outputs = namedtuple('Outputs', ['exit_status', 'stdout', 'stderr'])

forbidden_binaries = ['rm', 'mv', 'dd', 'wget', 'mkfs']


def get_env(env: typing.Optional[str] = None) -> dict:
    """ Get the environment variables to be used for the subprocess. """
    return {**os.environ, **(env or {})}


class Executable:
    """ Allow to execute a program and conveniently read the output. """

    def __new__(cls, filename):
        return super().__new__(cls) if filename else None

    def __init__(self, filename, encoding='utf-8', filters=None, env=None):
        self.filename = filename
        self.encoding = encoding
        self.env = get_env(env)
        self.filters = filters or {}

        if not self._is_executable(filename):
            if '/' not in filename and shutil.which(filename) is not None:
                if filename in forbidden_binaries:
                    raise ValueError(f"Program '{filename}' is forbidden!")
                filename = shutil.which(filename)
            else:
                raise ValueError(f"Program '{filename}' is not an executable!")

    def run(self, *args, stdin=None):
        """ Run the program and grab all the outputs. """
        with subprocess.Popen([self.filename, *[str(a) for a in args]],
                              stdout=subprocess.PIPE,
                              stdin=subprocess.PIPE,
                              stderr=subprocess.PIPE, env=self.env) as proc:

            if stdin is not None:
                stdin = stdin.encode(self.encoding)

            stdout, stderr = proc.communicate(input=stdin)

            if stdout is not None:
                stdout = stdout.decode(self.encoding)
            if stderr is not None:
                stderr = stderr.decode(self.encoding)

            stdout = self._filter(self.filters, stdout)
            stderr = self._filter(self.filters, stderr)

            return Outputs(
                proc.returncode,
                GreppableString(stdout),
                GreppableString(stderr))

    def __call__(self, *args, **kwargs):
        return self.run(*args, **kwargs)

    @staticmethod
    def _is_executable(filename):
        return os.path.isfile(filename) and os.access(filename, os.X_OK)

    def _filter(self, filters: typing.Dict, value: str) -> str:
        return apply_filters(value, filters)


class GreppableString(str):
    """ A string that can be parsed with regular expressions. """

    def grep(self, pattern: str) -> bool:
        """ Return True if the pattern is found in the string. """
        return re.findall(pattern, self)

    def contains(self, value: str) -> bool:
        """ Return True if the value is found in the string. """
        return value in self
