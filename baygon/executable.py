""" Executable class. To be used with the Test class. """

import os
import shutil
import typing
import subprocess
from pathlib import Path
from collections import namedtuple
Outputs = namedtuple('Outputs', ['exit_status', 'stdout', 'stderr'])

forbidden_binaries = ['rm', 'mv', 'dd', 'wget', 'mkfs']


def get_env(env: typing.Optional[str] = None) -> dict:
    """ Get the environment variables to be used for the subprocess. """
    return {**os.environ, **(env or {})}


class Executable:
    """ Allow to execute a program and conveniently read the output. """

    def __new__(cls, filename):
        if isinstance(filename, cls):
            return filename

        return super().__new__(cls) if filename else None

    def __init__(self, filename, encoding='utf-8'):
        if isinstance(filename, self.__class__):
            self.filename = filename.filename
            self.encoding = filename.encoding
        else:
            self.filename = filename
            self.encoding = encoding

        if not self._is_executable(self.filename):
            if '/' not in filename and shutil.which(filename) is not None:
                if filename in forbidden_binaries:
                    raise ValueError(f"Program '{filename}' is forbidden!")
                filename = shutil.which(filename)
            else:
                raise ValueError(f"Program '{filename}' is not an executable!")

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
