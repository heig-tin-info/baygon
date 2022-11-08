""" Main CLI command. """
import logging
import os
import sys
import time

import click

from . import TestCase, TestGroup, TestSuite, __copyright__, __version__
from .error import InvalidExecutableError


def display_pad(pad=0):
    """ Display a pad of spaces to align nested output. """
    click.secho('.' * pad if pad > 0 else '  ', nl=False, dim=pad == 0)


def test_name_length(test):
    """ Compute the length of test name. """
    return len(f'{test.id.pad()}Test {test.id}: {test.name}')


def display_test_name(test):
    """ Display the name of a test. """
    click.secho(f'{test.id.pad()}Test {test.id}: ', nl=False, bold=True)
    click.secho(f'{test.name}', nl=False, bold=False)


class OneLineExceptionFormatter(logging.Formatter):
    """ A formatter that displays the exception on a single line. """

    def format_exception(self, exc_info):
        """ Format an exception. """
        result = super().format_exception(exc_info)
        return repr(result)

    def format(self, record):
        """ Format a log record. """
        result = super().format(record)
        if record.exc_text:
            result = result.replace("\n", "")
        return result


class Runner:
    """ Test runner. """

    def __init__(self, executable=None, config=None, **kwargs):
        self.verbose = kwargs.get('verbose', 0)
        if self.verbose > 3:
            self._init_logger("DEBUG")

        self.executable = executable
        self.limit = kwargs.get('limit', -1)
        click.secho(config, fg='yellow')
        self.test_suite = TestSuite(path=config, executable=self.executable)

        self.align_column = 0

        self.failures = 0
        self.successes = 0
        self.skipped = 0

    def _init_logger(self, loglevel):
        handler = logging.StreamHandler()
        formatter = OneLineExceptionFormatter(logging.BASIC_FORMAT)
        handler.setFormatter(formatter)
        root = logging.getLogger()
        root.setLevel(os.environ.get("LOGLEVEL", loglevel))
        root.addHandler(handler)

    def run(self):
        """ Run the tests. """
        start_time = time.time()
        self.align_column = self._max_length(self.test_suite) + 10

        self.failures = 0
        self.successes = 0
        self.skipped = 0

        self._traverse_group(self.test_suite)

        tests = self.failures + self.successes + self.skipped
        seconds = round(time.time() - start_time, 2)
        click.secho(f'\nRan {tests} tests in {seconds}s.', bold=True)

        if self.failures > 0:
            ratio = 100 - round(
                self.failures / (self.failures + self.successes) * 100, 2)
            click.secho((f'{self.failures} failed, {self.successes} '
                         f'passed ({ratio}%% ok).'), fg='yellow', bold=True)
            click.secho('\nfail.', fg='red', bold=True)
        else:
            click.secho('\nok.', fg='green')

        if self.skipped > 0:
            click.secho((
                f'{self.skipped} test(s) skipped, '
                'some executables may be missing.'), fg='yellow')

        return self.failures

    def _max_length(self, tests):
        length = 0
        for test in tests:
            length = max(test_name_length(test), length)
            if isinstance(test, TestGroup):
                length = max(self._max_length(test), length)
        return length

    def _traverse_group(self, tests):
        for test in tests:
            if self.limit > 0 and self.failures > self.limit:
                break

            if isinstance(test, TestGroup):
                display_test_name(test)
                click.echo('')
                self._traverse_group(test)
            elif isinstance(test, TestCase):
                display_test_name(test)
                issues = test.run()
                if issues is None:  # Skipped
                    click.secho(' SKIPPED', fg='yellow')
                    self.skipped += 1
                    continue
                display_pad(self.align_column - test_name_length(test))
                if not issues:
                    self.successes += 1
                    click.secho(' PASSED', fg='green')
                else:
                    self.failures += 1
                    click.secho(' FAILED', fg='red', bold=True)
                    for issue in issues:
                        click.secho('  ' * len(test.id) + '- ' + str(issue),
                                    fg='magenta')
        return self.failures


def version():
    """ Display the version. """
    print(f"Baygon version {__version__} {__copyright__}")


@click.command()
@click.argument('executable', required=False, type=click.Path(exists=True))
@click.option('--version', is_flag=True, help='Shows version')
@click.option('-v', '--verbose', count=True, help='Shows more details')
@click.option('-l', '--limit', type=int, default=-1, help='Limit errors to N')
@click.option('-d', '--debug', is_flag=True, default=0, help='Debug mode')
@click.option('-t', '--config',
              type=click.Path(exists=True),
              help='Choose config file (.yml or .json)')
def cli(debug, verbose=0, executable=None, config=None, **kwargs):
    """ Baygon functional test runner. """
    if kwargs.get('version'):
        version()
        sys.exit(0)

    if debug:
        failures = Runner(executable, config, verbose=verbose, **kwargs).run()
    else:
        try:
            failures = Runner(executable, config, verbose=verbose, **kwargs).run()
        except InvalidExecutableError as error:
            click.secho(f"\nError: {error}", fg='red', bold=True, err=True)
            sys.exit(1)

    click.echo('')
    return failures


if __name__ == '__main__':
    cli()
