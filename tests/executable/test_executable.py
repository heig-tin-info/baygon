import shutil
import subprocess
from pathlib import Path

import pytest

from baygon.executable import Executable, is_safe_executable
from baygon.error import InvalidExecutableError
from baygon.helpers import GreppableString

dir_path = Path(__file__).resolve(strict=True).parent


def test_not_a_file():
    with pytest.raises(InvalidExecutableError):
        Executable("not-a-file")


def test_arg():
    e = Executable(shutil.which("echo"))
    test_string = "Live as if you were to die tomorrow"
    output = e.run("-n", test_string)
    # Vérification que l'output est égal à la chaîne testée
    assert output.stdout == test_string


def test_stdout():
    e = Executable(dir_path.joinpath("dummy.exe.py"))
    output = e.run()
    # Vérification que stdout contient bien "an apple"
    assert output.stdout == "an apple\n"


def test_stderr():
    e = Executable(dir_path.joinpath("dummy.exe.py"))
    output = e.run()
    # Vérification que stderr contient bien "an orange"
    assert output.stderr == "an orange\n"


def test_stdin():
    e = Executable(shutil.which("cat"))
    test_string = "Live as if you were to die tomorrow"
    output = e.run(stdin=test_string)
    # Vérification que l'input est renvoyé en sortie
    assert output.stdout == test_string


def test_exit_status():
    e = Executable(dir_path.joinpath("dummy.exe.py"))
    output = e.run()
    # Vérification que le code de sortie est 42
    assert output.exit_status == 42


def test_args():
    e = Executable(dir_path.joinpath("args.exe.py"))
    test_string = "foobar"
    output = e.run(2, test_string)
    # Vérification que la sortie contient bien "foobar" avec un saut de ligne
    assert output.stdout == test_string + "\n"


def test_grep():
    s = GreppableString("Live as if you were to die tomorrow")
    u = s.grep(r"\b[aeiouy]\w{2}\b")
    # Vérification que le résultat du grep est bien ["you"]
    assert u == ["you"]


def test_echo():
    e = Executable("echo")
    test_string = "Live as if you were to die tomorrow"
    output = e.run(test_string)
    # Vérification que la sortie de echo contient bien la chaîne avec un saut de ligne
    assert output.stdout == test_string + "\n"


def test_printf():
    e = Executable("printf")
    test_string = "Live as if you were to die tomorrow"
    output = e.run(test_string)
    # Vérification que printf sort exactement la chaîne testée sans saut de ligne
    assert output.stdout == test_string


def test_cat():
    e = Executable("cat")
    output = e.run(dir_path.joinpath("test.txt"))
    # Vérification que la sortie de cat est "Hello World\n"
    assert output.stdout == "Hello World\n"


def test_executable_echo():
    e = Executable("echo")
    result = e("Hello", "World")
    assert result.exit_status == 0
    assert result.stdout.strip() == "Hello World"
    assert result.stderr == ""


def test_executable_invalid_program():
    with pytest.raises(InvalidExecutableError):
        Executable("invalid_program")


def test_executable_with_cwd():
    cwd = "/tmp"
    e = Executable("ls", cwd=cwd)
    assert e.get_cwd() == cwd


def test_executable_use_tty():
    e = Executable("echo")
    result = e("Hello World", use_tty=True)
    assert result.exit_status == 0
    assert result.stdout.strip() == "Hello World"


def test_executable_with_timeout():
    e = Executable("sleep")
    with pytest.raises(subprocess.TimeoutExpired):
        e("5", timeout=1)


def test_safe_executable_checks():
    with pytest.raises(InvalidExecutableError):
        Executable("rm").run("/*")


def test_environment_variable_injection():
    e = Executable("echo")
    env = {"TEST_ENV": "123"}
    result = e("$TEST_ENV", env=env)
    assert result.stdout.strip() == "123"


def test_safe_executable():
    assert not is_safe_executable("ls", ["sudo"])
    assert is_safe_executable("rm", ["test.txt"])
    assert not is_safe_executable("rm", ["/*"])
    assert not is_safe_executable("mkfs", [])
    assert not is_safe_executable("fdisk", ["-l"])
    assert not is_safe_executable("dd", ["if=/dev/sda", "of=/dev/sdb"])
    assert not is_safe_executable("iptables", ["-F"])
