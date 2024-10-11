import logging
import os
import pty
import shutil
import subprocess
import time
import typing
from collections import namedtuple
from pathlib import Path

from .error import InvalidExecutableError

logger = logging.getLogger("baygon")

Outputs = namedtuple("Outputs", ["exit_status", "stdout", "stderr", "time"])


def is_safe_executable(filename: str, args: typing.List[str] = []) -> bool:
    """Check if the executable with the given arguments is safe to use."""

    dangerous_executables = [
        "rm",
        "mv",
        "dd",
        "wget",
        "mkfs",
        "fdisk",
        "parted",
        "shutdown",
        "reboot",
        "poweroff",
        "kill",
        "killall",
        "iptables",
        "ufw",
        "passwd",
        "useradd",
        "userdel",
        "chmod",
        "chown",
        "sudo",
    ]

    dangerous_args = {
        "rm": ["/*", "--no-preserve-root"],
        "mv": ["/*"],
        "dd": ["if=/dev/sda", "of=/dev/sda"],
        "mkfs": [],
        "fdisk": [],
        "shutdown": ["now"],
        "reboot": ["now"],
        "iptables": ["-F", "--flush"],
        "ufw": ["reset"],
    }

    if filename in dangerous_executables:
        return False

    if filename in dangerous_args:
        for arg in args:
            if arg in dangerous_args[filename]:
                return False

    if "sudo" in args:
        return False

    return True


def get_env(env: typing.Optional[dict] = None) -> dict:
    """Get the environment variables to be used for the subprocess."""
    return {**os.environ, **(env or {})}


class Executable:
    """An executable program.

    Convenient execution and access to program outputs such as:

        - Exit status
        - Standard output
        - Standard error

    For example:

        >>> e = Executable('echo')
        >>> e
        Executable<echo>
        >>> e('-n', 'Hello World')
        Outputs(exit_status=0, stdout='Hello World', stderr='')
        >>> e('-n', 'Hello World').stdout
        'Hello World'
    """

    def __new__(cls, filename):
        if isinstance(filename, cls):
            return filename

        return super().__new__(cls) if filename else None

    def __init__(self, filename, encoding="utf-8", cwd=None):
        """Create an executable object.

        :param filename: The path of the executable.
        :param encoding: The encoding to be used for the outputs, default is UTF-8.
        :param cwd: The working directory, default is None (current directory).
        """
        if isinstance(filename, self.__class__):
            self.filename = filename.filename
            self.encoding = filename.encoding
            self.cwd = filename.cwd
        else:
            self.filename = filename
            self.encoding = encoding
            self.cwd = cwd or os.getcwd()

        if not self._is_executable(self.filename):
            if "/" not in filename and shutil.which(filename) is not None:
                if not is_safe_executable(filename):
                    raise InvalidExecutableError(f"Program '{filename}' is forbidden!")
                filename = shutil.which(filename)
            else:
                raise InvalidExecutableError(
                    f"Program '{filename}' is not an executable!"
                )

    def run(self, *args, stdin=None, env=None, hook=None, timeout=None, use_tty=False):
        cmd = [self.filename, *map(str, args)]

        start_time = time.time()  # Mesure du début de l'exécution

        # Choix des paramètres de subprocess en fonction de use_tty
        popen_args = {
            "stdout": subprocess.PIPE,
            "stderr": subprocess.PIPE,
            "env": env,
            "cwd": self.cwd,
        }

        if use_tty:
            master_fd, slave_fd = pty.openpty()
            popen_args.update({"stdin": slave_fd})
        else:
            popen_args.update({"stdin": subprocess.PIPE})

        try:
            with subprocess.Popen(cmd, **popen_args) as proc:
                if stdin is not None:
                    stdin = stdin.encode(self.encoding)
                    if use_tty:
                        os.write(master_fd, stdin)

                stdout, stderr = proc.communicate(
                    input=stdin if not use_tty else None, timeout=timeout
                )

                stdout = stdout.decode(self.encoding) if stdout else ""
                stderr = stderr.decode(self.encoding) if stderr else ""

            execution_time = time.time() - start_time  # Mesure du temps d'exécution

            if hook and callable(hook):
                hook(
                    cmd=cmd,
                    stdin=stdin,
                    stdout=stdout,
                    stderr=stderr,
                    exit_status=proc.returncode,
                    execution_time=execution_time,
                )

            return Outputs(proc.returncode, stdout, stderr, execution_time)

        except subprocess.TimeoutExpired:
            proc.kill()
            raise

        except subprocess.TimeoutExpired:
            proc.kill()
            raise

    def __call__(self, *args, **kwargs):
        return self.run(*args, **kwargs)

    def __repr__(self):
        return f"{self.__class__.__name__}<{self.filename}>"

    @staticmethod
    def _is_executable(filename):
        path = Path(filename)
        return path.is_file() and os.access(path, os.X_OK)

    def get_cwd(self):
        """Return the current working directory for this executable."""
        return self.cwd
