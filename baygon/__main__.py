import click
import time
import json
import logging
import os


from . import TestSuite, TestCase, Tests, validation, Executable


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
    click.echo(f'{test.name}', nl=False)


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
    def __init__(self, verbose, executable=None, **kwargs):
        if verbose > 3:
            self._init_logger("DEBUG")

        self.verbose = verbose
        self.executable = executable
        self.limit = -1 if 'limit' not in kwargs else kwargs['limit']
        self.filename = validation.find_testfile()
        self.test_description = Tests(self.filename)
        self.test_suite = TestSuite(
            self.test_description, Executable(self.executable))

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

        self._traverse_group(self.test_suite)


        click.secho('\nRan %d tests in %ss.' % (
            self.successes + self.failures,
            round(time.time() - start_time, 2)
        ), bold=True)

        if self.failures > 0:
            click.secho('%d failed, %d passed (%d%% ok).' % (
                self.failures, self.successes,
                100-round(self.failures/self.successes*100, 2)), fg='yellow', bold=True)
            click.secho('\nfail.', fg='red', bold=True)
        else:
            click.secho('\nok.', fg='green')

        return self.failures

    def _max_length(self, tests):
        length = 0
        for test in tests:
            if isinstance(test, TestSuite):
                length = max(test_name_length(test), length)
                length = max(self._max_length(test), length)
            else:
                length = max(test_name_length(test), length)
        return length

    def _traverse_group(self, tests):
        for test in tests:
            if self.limit > 0 and self.failures > self.limit:
                break

            if isinstance(test, TestSuite):
                display_test_name(test)
                click.echo('')
                self._traverse_group(test)
            elif isinstance(test, TestCase):
                display_test_name(test)
                issues = test.run()
                display_pad(self.align_column - test_name_length(test))
                if not len(issues):
                    self.successes += 1
                    click.secho(' PASSED', fg='green')
                else:
                    self.failures += 1
                    click.secho(' FAILED', fg='red', bold=True)
                    for issue in issues:
                        click.secho('  ' * len(test._id) + '- ' + 
                                    str(issue), fg='magenta', bold=True)
        return self.failures


@click.command()
@click.argument('executable', required=False, type=click.Path(exists=True))
@click.option('-v', '--verbose', count=True)
@click.option('-l', '--limit', type=int, default=-1)
def cli(verbose=0, executable=None, **kwargs):
    runner = Runner(verbose, executable, **kwargs)
    failures = runner.run()
    click.echo('')
    return failures


if __name__ == '__main__':
    cli()
