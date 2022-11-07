""" Test CLI. """
from unittest import TestCase
from pathlib import Path
from click.testing import CliRunner
from baygon.__main__ import cli


class TestVersion(TestCase):
    def test_version(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['--version'])

        self.assertEqual(result.exit_code, 0)
        self.assertIn('version', result.output)


class TestDemo(TestCase):
    def dir_path(self):
        return Path(__file__).absolute().parent

    def test_success(self):
        runner = CliRunner()
        dir_path = self.dir_path()
        config = dir_path.joinpath('success.yml')
        executable = dir_path.joinpath('main.py')
        print(f"dir_path: {dir_path}")
        print(f"config: {config}")
        result = runner.invoke(cli, [f"--config={config}", executable, '-v'])

        print(f"Output: {result}")
        print(f"Stdout: {result.stdout}")
        print(f"Stderr: {result.stderr}")

        self.assertEqual(result.exit_code, 0)
        self.assertIn('Ran 4 tests in', result.output)
        self.assertIn('ok.', result.output)

    def test_failure(self):
        runner = CliRunner()
        dir_path = self.dir_path()
        result = runner.invoke(
            cli, [
                f"--config={dir_path.joinpath('fail.yml')}",
                dir_path.joinpath('main.py'), '-v'])

        print(result)
        self.assertEqual(result.exit_code, 0)
        self.assertIn('Invalid exit status', result.output)
        self.assertIn('Invalid value on stdout', result.output)
        self.assertIn('fail.', result.output)

    def test_inverse(self):
        runner = CliRunner()
        dir_path = self.dir_path()
        result = runner.invoke(
            cli, [
                f"--config={dir_path.joinpath('inverse.yml')}",
                dir_path.joinpath('main.py'), '-v'])

        print(result, result.output)

        self.assertEqual(result.exit_code, 0)
        self.assertIn('ok.', result.output)

    def test_ignorespaces(self):
        runner = CliRunner()
        dir_path = self.dir_path()
        result = runner.invoke(
            cli, [
                f"--config={dir_path.joinpath('ignorespaces.yml')}",
                '--verbose',
                dir_path.joinpath('main2.py'), '-v'])

        print(result, result.output)

        self.assertEqual(result.exit_code, 0)
        self.assertIn('ok.', result.output)
