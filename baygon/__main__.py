import click
import time
import logging
import os

from . import TestSuite, TestGroup, TestCase, Executable
from . import __version__, __copyright__


def display_pad(pad=0):
    if pad == 0:
        click.secho('  ', nl=False)
    else:
        click.secho('.' * pad, nl=False, dim=True)


def test_name_length(test):
    pad = '  ' * (len(test._id) - 1)
    return len(f'{pad}Test {test.id}: {test.name}')


def display_test_name(test):
    pad = '  ' * (len(test._id) - 1)
    click.secho(f'{pad}Test {test.id}: ', nl=False, bold=True)
    click.secho(f'{test.name}', nl=False, bold=False)


class OneLineExceptionFormatter(logging.Formatter):
    def formatException(self, exc_info):
        result = super().formatException(exc_info)
        return repr(result)

    def format(self, record):
        result = super().format(record)
        if record.exc_text:
            result = result.replace("\n", "")
        return result


class Runner:
    def __init__(self, verbose, executable=None, config=None, **kwargs):
        if verbose > 3:
            self._init_logger("DEBUG")

        self.verbose = verbose
        self.executable = executable
        self.limit = -1 if 'limit' not in kwargs else kwargs['limit']
        self.test_suite = TestSuite(path=config, executable=Executable(self.executable))

    def _init_logger(self, loglevel):
        handler = logging.StreamHandler()
        formatter = OneLineExceptionFormatter(logging.BASIC_FORMAT)
        handler.setFormatter(formatter)
        root = logging.getLogger()
        root.setLevel(os.environ.get("LOGLEVEL", loglevel))
        root.addHandler(handler)

    def run(self):
        start_time = time.time()
        self.align_column = self._max_length(self.test_suite) + 10

        self.failures = 0
        self.successes = 0
        self.skipped = 0

        self._traverse_group(self.test_suite)

        click.secho('\nRan %d tests in %ss.' % (
            self.successes + self.failures,
            round(time.time() - start_time, 2)
        ), bold=True)

        if self.failures > 0:
            click.secho('%d failed, %d passed (%d%% ok).' % (
                self.failures, self.successes,
                100 - round(self.failures / (self.failures + self.successes) * 100, 2)
            ), fg='yellow', bold=True)
            click.secho('\nfail.', fg='red', bold=True)
        else:
            click.secho('\nok.', fg='green')

        if self.skipped > 0:
            click.secho(
                f'{self.skipped} test(s) skipped, some executables may be missing.', fg='yellow')

        return self.failures

    def _max_length(self, tests, level=0):
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
                if not len(issues):
                    self.successes += 1
                    click.secho(' PASSED', fg='green')
                else:
                    self.failures += 1
                    click.secho(' FAILED', fg='red', bold=True)
                    for issue in issues:
                        click.secho('  ' * len(test._id) + '- ' + str(issue),
                                    fg='magenta', bold=True)
        return self.failures


def version(ctx, param, value):
    if not value:
        return
    print(f"Baygon version {__version__} {__copyright__}")
    exit(0)


@click.command()
@click.argument('executable', required=False, type=click.Path(exists=True))
@click.option('--version', is_flag=True, callback=version, help='Shows version')
@click.option('-v', '--verbose', count=True, help='Shows more details')
@click.option('-l', '--limit', type=int, default=-1, help='Limit to N tests')
@click.option('-t', '--config',
              type=click.Path(exists=True),
              help='Choose config file (.yml or .json)')
def cli(verbose=0, executable=None, config=None, **kwargs):
    runner = Runner(verbose, executable, config, **kwargs)
    failures = runner.run()
    click.echo('')
    return failures


if __name__ == '__main__':
    cli()
