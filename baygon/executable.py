""" Executable class. To be used with the Test class. """

import os
import shutil
import subprocess
import typing
from collections import namedtuple
from pathlib import Path
from .error import InvalidExecutableError

Outputs = namedtuple('Outputs', ['exit_status', 'stdout', 'stderr'])

forbidden_binaries = ['rm', 'mv', 'dd', 'wget', 'mkfs']


def get_env(env: typing.Optional[str] = None) -> dict:
    """ Get the environment variables to be used for the subprocess. """
    return {**os.environ, **(env or {})}


class Executable:
    """ An executable program.

    Convenient execution and access to program outputs such as:

        - Exit status
        - Standard output
        - Standard error

    For example:

        >>> e = Executable('echo')
        Executable<echo>
        >>> e('-n', 'Hello World')
        Outputs(exit_status=0, stdout='Hello World', stderr='')
        >>> e('-n', 'Hello World').stdout
        'Hello World!'
    """

    def __new__(cls, filename):
        if isinstance(filename, cls):
            return filename

        return super().__new__(cls) if filename else None

    def __init__(self, filename, encoding='utf-8'):
        """ Create an executable object.

        :param filename: The path of the executable.
        :param encoding: The encoding to be used for the outputs, default is UTF-8.
        """
        if isinstance(filename, self.__class__):
            self.filename = filename.filename
            self.encoding = filename.encoding
        else:
            self.filename = filename
            self.encoding = encoding

        if not self._is_executable(self.filename):
            if '/' not in filename and shutil.which(filename) is not None:
                if filename in forbidden_binaries:
                    raise InvalidExecutableError(f"Program '{filename}' is forbidden!")
                filename = shutil.which(filename)
            else:
                raise InvalidExecutableError(f"Program '{filename}' is not an executable!")

    def run(self, *args, stdin=None, env=None):
        """ Run the program and grab all the outputs. """
        with subprocess.Popen([self.filename, *[str(a) for a in args]],
                              stdout=subprocess.PIPE,
                              stdin=subprocess.PIPE,
                              stderr=subprocess.PIPE, env=env) as proc:

            if stdin is not None:
                stdin = stdin.encode(self.encoding)

            stdout, stderr = proc.communicate(input=stdin)

            if stdout is not None:
                stdout = stdout.decode(self.encoding)
            if stderr is not None:
                stderr = stderr.decode(self.encoding)

            return Outputs(
                proc.returncode,
                stdout,
                stderr)

    def __call__(self, *args, **kwargs):
        return self.run(*args, **kwargs)

    def __repr__(self):
        return f"{self.__class__.__name__}<{self.filename}>"

    @staticmethod
    def _is_executable(filename):
        path = Path(filename)
        return path.is_file() and os.access(path, os.X_OK)
