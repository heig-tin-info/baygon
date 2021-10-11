from click.testing import CliRunner
from unittest import TestCase
from baygon.__main__ import cli
import os


class TestVersion(TestCase):
    def test_version(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['--version'])

        self.assertEqual(result.exit_code, 0)
        self.assertIn('version', result.output)


class TestDemo(TestCase):
    def test_success(self):
        runner = CliRunner()
        dir_path = os.path.dirname(os.path.realpath(__file__))
        result = runner.invoke(
            cli, [
                '--config=' + os.path.join(dir_path, 'success.yml'),
                os.path.join(dir_path, 'main.py'), '-v'])

        print(result.output)

        self.assertEqual(result.exit_code, 0)
        self.assertIn('Ran 4 tests in', result.output)
        self.assertIn('ok.', result.output)

    def test_failure(self):
        runner = CliRunner()
        dir_path = os.path.dirname(os.path.realpath(__file__))
        result = runner.invoke(
            cli, [
                '--config=' + os.path.join(dir_path, 'fail.yml'),
                os.path.join(dir_path, 'main.py'), '-v'])

        print(result.output)
        self.assertEqual(result.exit_code, 0)
        self.assertIn('Invalid exit status', result.output)
        self.assertIn('Invalid value on stdout', result.output)
        self.assertIn('fail.', result.output)

    def test_inverse(self):
        runner = CliRunner()
        dir_path = os.path.dirname(os.path.realpath(__file__))
        result = runner.invoke(
            cli, [
                '--config=' + os.path.join(dir_path, 'inverse.yml'),
                os.path.join(dir_path, 'main.py'), '-v'])

        print(result, result.output)

        self.assertEqual(result.exit_code, 0)
        self.assertIn('ok.', result.output)

    def test_ignorespaces(self):
        runner = CliRunner()
        dir_path = os.path.dirname(os.path.realpath(__file__))
        result = runner.invoke(
            cli, [
                '--config=' + os.path.join(dir_path, 'ignorespaces.yml'),
                '--verbose',
                os.path.join(dir_path, 'main2.py'), '-v'])

        print(result, result.output)

        self.assertEqual(result.exit_code, 0)
        self.assertIn('ok.', result.output)
