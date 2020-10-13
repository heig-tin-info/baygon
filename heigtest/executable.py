import os
import re
import sys
import subprocess

from collections import namedtuple


Outputs = namedtuple('Outputs', ['exit_status', 'stdout', 'stderr'])


class Executable:
    def __init__(self, filename):
        self.filename = filename

        if not self._is_executable(filename):
            raise ValueError("Program %s is not executable!" % filename)

    def run(self, *args, stdin=None):
        p = subprocess.Popen([self.filename, *[str(a) for a in args]],
                             stdout=subprocess.PIPE,
                             stdin=subprocess.PIPE,
                             stderr=subprocess.STDOUT)

        stdout, stderr = p.communicate(input=stdin)

        return Outputs(p.returncode, GreppableString(stdout), GreppableString(stderr))

    def __call__(self, *args, **kwargs):
        return self.run(*args, **kwargs)

    @staticmethod
    def _is_executable(filename):
        return os.path.isfile(filename) and os.access(filename, os.X_OK)


class GreppableString(str):
    def grep(self, pattern):
        return re.findall(pattern, self)
