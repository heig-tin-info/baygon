import shutil
from pathlib import Path
from unittest import TestCase

from baygon import Executable
from baygon.str import GreppableString
from baygon.error import InvalidExecutableError

dir_path = Path(__file__).resolve(strict=True).parent


class TestExecutable(TestCase):
    def test_not_a_file(self):
        self.assertRaises(InvalidExecutableError, Executable, 'not-a-file')

    def test_arg(self):
        e = Executable(shutil.which('echo'))
        test_string = 'Live as if you were to die tomorrow'
        output = e.run('-n', test_string)
        print(output)
        self.assertEqual(output.stdout, test_string)

    def test_stdout(self):
        e = Executable(dir_path.joinpath('dummy.py'))
        output = e.run()
        print(output)
        self.assertEqual(output.stdout, "an apple\n")

    def test_stderr(self):
        e = Executable(dir_path.joinpath('dummy.py'))
        output = e.run()
        print(output)
        self.assertEqual(output.stderr, "an orange\n")

    def test_stdin(self):
        e = Executable(shutil.which('cat'))
        test_string = 'Live as if you were to die tomorrow'
        output = e.run(stdin=test_string)
        print(output)
        self.assertEqual(output.stdout, test_string)

    def test_exit_status(self):
        e = Executable(dir_path.joinpath('dummy.py'))
        output = e.run()
        print(output)
        self.assertEqual(output.exit_status, 42)

    def test_args(self):
        e = Executable(dir_path.joinpath('args.py'))
        test_string = 'foobar'
        output = e.run(2, test_string)
        print(output)
        self.assertEqual(output.stdout, test_string + '\n')

    def test_grep(self):
        s = GreppableString('Live as if you were to die tomorrow')
        u = s.grep(r'\b[aeiouy]\w{2}\b')
        print(u)
        self.assertEqual(u, ['you'])

    def test_echo(self):
        e = Executable('echo')
        test_string = 'Live as if you were to die tomorrow'
        output = e.run(test_string)
        print(output)
        self.assertEqual(output.stdout, test_string + "\n")

    def test_printf(self):
        e = Executable('printf')
        test_string = 'Live as if you were to die tomorrow'
        output = e.run(test_string)
        print(output)
        self.assertEqual(output.stdout, test_string)

    def test_cat(self):
        e = Executable('cat')
        output = e.run(dir_path.joinpath('test.txt'))
        print(output)
        self.assertEqual(output.stdout, "Hello World\n")
