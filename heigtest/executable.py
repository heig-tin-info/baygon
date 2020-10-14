import os
import re
import sys
import subprocess

from collections import namedtuple


Outputs = namedtuple('Outputs', ['exit_status', 'stdout', 'stderr'])


class Executable:
    """ Allow to execute a program and conveniently read the output. """
    def __init__(self, filename, encoding='utf-8'):
        self.filename = filename
        self.encoding = encoding

        if not self._is_executable(filename):
            raise ValueError("Program %s is not executable!" % filename)

    def run(self, *args, stdin=None):
        p = subprocess.Popen([self.filename, *[str(a) for a in args]],
                             stdout=subprocess.PIPE,
                             stdin=subprocess.PIPE,
                             stderr=subprocess.PIPE)

        stdout, stderr = p.communicate(input=stdin)

        stdout = stdout.decode(self.encoding) if stdout is not None else None
        stderr = stderr.decode(self.encoding) if stderr is not None else None

        return Outputs(p.returncode, GreppableString(stdout), GreppableString(stderr))

    def __call__(self, *args, **kwargs):
        return self.run(*args, **kwargs)

    @staticmethod
    def _is_executable(filename):
        return os.path.isfile(filename) and os.access(filename, os.X_OK)


class GreppableString(str):
    """ A string that can be parsed with regular expressions. """
    def grep(self, pattern):
        return re.findall(pattern, self)
