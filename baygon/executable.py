"""Executable class. To be used with the Test class."""

from collections import namedtuple
import contextlib
import logging
import os
from pathlib import Path
import shutil
import signal
import subprocess
import threading
import time
import typing

from .error import InvalidExecutableError

logger = logging.getLogger("baygon")

forbidden_binaries = ["rm", "mv", "dd", "wget", "mkfs"]

#: Default cap, in bytes, on what is kept from each output stream (stdout and
#: stderr). A program that prints without end is killed once it is reached,
#: so Baygon never holds an unbounded amount of output in memory.
DEFAULT_MAX_OUTPUT = 16 * 1024 * 1024

_READ_CHUNK = 64 * 1024

# Time given to the reader threads to collect what is left in the pipes once
# the program has been killed.
_KILL_GRACE = 2.0


class Outputs(namedtuple("Outputs", ["exit_status", "stdout", "stderr"])):
    """Outputs of a program run.

    It behaves as a ``(exit_status, stdout, stderr)`` tuple. Two extra
    attributes tell whether the run was cut short:

    - ``timed_out``: the program was killed after its time limit.
    - ``output_limit_exceeded``: the program was killed because one of its
      output streams went over the limit, the outputs are truncated.
    """

    timed_out = False
    output_limit_exceeded = False

    def __new__(
        cls,
        exit_status,
        stdout,
        stderr,
        *,
        timed_out=False,
        output_limit_exceeded=False,
    ):
        self = super().__new__(cls, exit_status, stdout, stderr)
        self.timed_out = timed_out
        self.output_limit_exceeded = output_limit_exceeded
        return self


def get_env(env: typing.Optional[str] = None) -> dict:
    """Get the environment variables to be used for the subprocess."""
    return {**os.environ, **(env or {})}


class _StreamReader(threading.Thread):
    """Drain a pipe into a bounded buffer."""

    def __init__(self, pipe, limit, on_overflow):
        super().__init__(daemon=True)
        self.pipe = pipe
        self.limit = limit
        self.on_overflow = on_overflow
        self.data = bytearray()
        self.overflow = False

    def run(self):
        try:
            while True:
                chunk = self.pipe.read1(_READ_CHUNK)
                if not chunk:
                    break
                if self.limit and len(self.data) + len(chunk) > self.limit:
                    self.data += chunk[: self.limit - len(self.data)]
                    self.overflow = True
                    self.on_overflow()
                    break
                self.data += chunk
        except (OSError, ValueError):  # pragma: no cover - pipe closed under us
            pass


def _feed_stdin(pipe, data):
    try:
        if data:
            pipe.write(data)
    except (BrokenPipeError, OSError, ValueError):
        pass  # The program exited or closed its input, nothing left to feed.
    finally:
        with contextlib.suppress(OSError, ValueError):
            pipe.close()


def _kill(proc):
    """Kill the program and every process it started."""
    if os.name == "posix":
        with contextlib.suppress(OSError):
            os.killpg(proc.pid, signal.SIGKILL)
    with contextlib.suppress(OSError):
        proc.kill()


class Executable:
    """An executable program.

    Convenient execution and access to program outputs such as:

        - Exit status
        - Standard output
        - Standard error

    For example:

        >>> e = Executable("echo")
        >>> e
        Executable<echo>
        >>> e("-n", "Hello World")
        Outputs(exit_status=0, stdout='Hello World', stderr='')
        >>> e("-n", "Hello World").stdout
        'Hello World'
    """

    def __new__(cls, filename, *_args, **_kwargs):
        if isinstance(filename, cls):
            return filename

        return super().__new__(cls) if filename else None

    def __init__(self, filename, encoding="utf-8"):
        """Create an executable object.

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
            if "/" not in filename and shutil.which(filename) is not None:
                if filename in forbidden_binaries:
                    raise InvalidExecutableError(f"Program '{filename}' is forbidden!")
                filename = shutil.which(filename)
            else:
                raise InvalidExecutableError(
                    f"Program '{filename}' is not an executable!"
                )

    def run(
        self,
        *args,
        stdin=None,
        env=None,
        hook=None,
        timeout=None,
        max_output=None,
    ):
        """Run the program and grab all the outputs.

        :param timeout: Wall-clock limit in seconds. Once reached, the program
            and the processes it started are killed and the returned outputs
            have ``timed_out`` set. ``None`` means no limit.
        :param max_output: Number of bytes kept from each output stream. Once
            a stream goes over it, the program is killed and the returned
            outputs have ``output_limit_exceeded`` set. ``None`` uses
            ``DEFAULT_MAX_OUTPUT``, ``0`` means no limit.
        """

        cmd = [self.filename, *[str(a) for a in args]]
        limit = DEFAULT_MAX_OUTPUT if max_output is None else int(max_output)

        if stdin is not None:
            stdin = stdin.encode(self.encoding)

        popen_kwargs = {}
        if os.name == "posix":
            # Own process group, so a timeout also kills the children.
            popen_kwargs["start_new_session"] = True

        with subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stdin=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            **popen_kwargs,
        ) as proc:
            try:
                stdout, stderr, timed_out, overflow = self._communicate(
                    proc, stdin, timeout, limit
                )
            except BaseException:
                # Never leave a running program behind (e.g. on Ctrl-C).
                _kill(proc)
                raise

            stdout = stdout.decode(self.encoding, errors="replace")
            stderr = stderr.decode(self.encoding, errors="replace")

            if hook and callable(hook):
                hook(
                    cmd=cmd,
                    stdin=stdin,
                    stdout=stdout,
                    stderr=stderr,
                    exit_status=proc.returncode,
                )

            return Outputs(
                proc.returncode,
                stdout,
                stderr,
                timed_out=timed_out,
                output_limit_exceeded=overflow,
            )

    @staticmethod
    def _communicate(proc, stdin, timeout, limit):
        killed = threading.Event()

        def _on_overflow():
            killed.set()
            _kill(proc)

        readers = [
            _StreamReader(proc.stdout, limit, _on_overflow),
            _StreamReader(proc.stderr, limit, _on_overflow),
        ]
        writer = threading.Thread(
            target=_feed_stdin, args=(proc.stdin, stdin), daemon=True
        )
        for thread in (*readers, writer):
            thread.start()

        deadline = None if timeout is None else time.monotonic() + timeout
        timed_out = False

        def _remaining():
            if deadline is None:
                return None
            return max(deadline - time.monotonic(), 0)

        try:
            proc.wait(timeout=_remaining())
        except subprocess.TimeoutExpired:
            timed_out = True
            _kill(proc)
            proc.wait()

        # The program is gone, but a child may still hold the pipes open.
        if timed_out or killed.is_set():
            grace = _KILL_GRACE
        elif deadline is not None:
            grace = max(_remaining(), 0.05)
        else:
            grace = None  # No time limit: wait as long as the pipes are open.
        for reader in readers:
            reader.join(grace)
        if any(reader.is_alive() for reader in readers):
            if not killed.is_set():
                timed_out = True
            _kill(proc)
            for reader in readers:
                reader.join(_KILL_GRACE)

        overflow = any(reader.overflow for reader in readers)
        return bytes(readers[0].data), bytes(readers[1].data), timed_out, overflow

    def __call__(self, *args, **kwargs):
        return self.run(*args, **kwargs)

    def __repr__(self):
        return f"{self.__class__.__name__}<{self.filename}>"

    @staticmethod
    def _is_executable(filename):
        path = Path(filename)
        return path.is_file() and os.access(path, os.X_OK)
