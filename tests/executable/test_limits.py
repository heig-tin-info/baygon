"""Time and output limits of Executable.run."""

from __future__ import annotations

import os
import pickle
import sys
import time

import pytest

from baygon import executable as executable_module
from baygon.executable import Executable, Outputs

python = Executable(sys.executable)


def test_outputs_still_behave_as_a_tuple() -> None:
    output = Outputs(1, "out", "err")
    exit_status, stdout, stderr = output
    assert (exit_status, stdout, stderr) == (1, "out", "err")
    assert output == (1, "out", "err")
    assert output.timed_out is False
    assert output.output_limit_exceeded is False
    assert repr(output) == "Outputs(exit_status=1, stdout='out', stderr='err')"
    assert output._replace(exit_status=2).timed_out is False

    flagged = pickle.loads(pickle.dumps(Outputs(0, "", "", timed_out=True)))
    assert flagged.timed_out is True


def test_timeout_kills_a_hanging_program() -> None:
    start = time.monotonic()
    output = python.run("-c", "import time; time.sleep(60)", timeout=0.3)
    assert time.monotonic() - start < 5
    assert output.timed_out is True
    assert output.output_limit_exceeded is False
    assert output.exit_status != 0


def test_timeout_keeps_partial_output() -> None:
    code = "import sys, time; print('started', flush=True); time.sleep(60)"
    output = python.run("-c", code, timeout=1)
    assert output.timed_out is True
    assert output.stdout == "started\n"


def test_program_reading_stdin_forever_gets_eof() -> None:
    output = python.run("-c", "import sys; sys.stdin.read()", timeout=10)
    assert output.timed_out is False
    assert output.exit_status == 0


@pytest.mark.skipif(os.name != "posix", reason="process groups are POSIX only")
def test_timeout_kills_child_processes() -> None:
    shell = Executable("sh")
    start = time.monotonic()
    # The grandchild keeps stdout open: without killing the whole group the
    # pipes would never close.
    output = shell.run("-c", "sleep 60 & sleep 60", timeout=0.3)
    assert time.monotonic() - start < 5
    assert output.timed_out is True


@pytest.mark.skipif(os.name != "posix", reason="process groups are POSIX only")
def test_background_child_holding_the_pipes_is_killed() -> None:
    shell = Executable("sh")
    start = time.monotonic()
    output = shell.run("-c", "sleep 60 & echo started", timeout=0.5)
    assert time.monotonic() - start < 2
    assert output.timed_out is True
    assert output.stdout == "started\n"


def test_fast_program_is_not_flagged() -> None:
    output = python.run("-c", "print('ok')", timeout=10)
    assert output == (0, "ok\n", "")
    assert output.timed_out is False


def test_output_limit_stops_an_endless_printer() -> None:
    code = "while True: print('menu')"
    output = python.run("-c", code, max_output=1000, timeout=30)
    assert output.output_limit_exceeded is True
    assert output.timed_out is False
    assert len(output.stdout) == 1000


def test_output_limit_applies_to_stderr() -> None:
    code = "import sys\nwhile True: sys.stderr.write('x' * 100)"
    output = python.run("-c", code, max_output=500, timeout=30)
    assert output.output_limit_exceeded is True
    assert len(output.stderr) == 500


def test_default_output_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(executable_module, "DEFAULT_MAX_OUTPUT", 2000)
    output = python.run("-c", "while True: print('x' * 50)", timeout=30)
    assert output.output_limit_exceeded is True
    assert len(output.stdout) == 2000


def test_zero_disables_the_output_limit() -> None:
    output = python.run("-c", "print('x' * 5000, end='')", max_output=0)
    assert output.output_limit_exceeded is False
    assert len(output.stdout) == 5000


def test_output_at_the_limit_is_accepted() -> None:
    output = python.run("-c", "print('x' * 99)", max_output=100)
    assert output.output_limit_exceeded is False
    assert output.stdout == "x" * 99 + "\n"


def test_large_stdin_ignored_by_the_program() -> None:
    output = python.run("-c", "pass", stdin="x" * 5_000_000, timeout=30)
    assert output.exit_status == 0
    assert output.timed_out is False


def test_invalid_utf8_output_does_not_crash() -> None:
    code = "import sys; sys.stdout.buffer.write(b'ok\\xff')"
    output = python.run("-c", code)
    assert output.stdout == "ok�"


def test_encoding_can_be_chosen() -> None:
    latin = Executable(sys.executable, encoding="latin-1")
    code = "import sys; sys.stdout.buffer.write(b'\\xe9')"
    assert latin.run("-c", code).stdout == "é"


def test_program_is_killed_when_interrupted(monkeypatch: pytest.MonkeyPatch) -> None:
    killed: list[int] = []
    real_kill = executable_module._kill

    def _interrupt(*args, **kwargs):
        raise KeyboardInterrupt

    def _spy_kill(proc) -> None:
        killed.append(proc.pid)
        real_kill(proc)

    monkeypatch.setattr(Executable, "_communicate", staticmethod(_interrupt))
    monkeypatch.setattr(executable_module, "_kill", _spy_kill)
    with pytest.raises(KeyboardInterrupt):
        python.run("-c", "import time; time.sleep(60)")
    assert len(killed) == 1


def test_hook_receives_the_run() -> None:
    calls: list[dict] = []
    python.run("-c", "print('hi')", hook=lambda **kw: calls.append(kw), timeout=10)
    assert calls[0]["stdout"] == "hi\n"
    assert calls[0]["exit_status"] == 0
