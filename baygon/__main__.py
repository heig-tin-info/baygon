import click
import time
import json
import logging
import os


from . import TestSuite, TestCase, Tests, validation, Executable


def pad_size(tests):
    width, _ = click.get_terminal_size()
    max_test_len = 0
    for t in tests:
        if len(t.name) > max_test_len:
            max_test_len = len(t.name)
    max_display_len = max_test_len + len('Test %d: PASSED' % len(tests))
    if width > max_display_len:
        return max_display_len
    return 0


def display_pad(pad=0):
    if pad == 0:
        click.secho('  ', nl=False)
    else:
        click.secho('.' * pad, nl=False, dim=True)


def display_pass(test, pad=0):
    display_pad(pad - len(test.name) - len(str(test.id)))
    click.secho(' PASSED', fg='green')


def display_fail(test, pad=0):
    display_test_name(test)
    display_pad(pad - len(test.name) - len(str(test.id)))
    click.secho(' FAILED', fg='red')


def test_name_length(test):
    pad = '  ' * (len(test.id) - 1)
    return len(f'{pad}Test {test.id}: {test.name}')


def display_test_name(test):
    pad = '  ' * (len(test.id) - 1)
    click.secho(f'{pad}Test {test.id}: ', nl=False, bold=True)
    click.echo(f'{test.name}', nl=False)


def display_failure(test, failures, pad, verbose=0):
    display_fail(test, pad)
    for f in failures:
        click.secho('  - ' + str(f), fg='yellow')
        if verbose > 1:
            click.secho(f.got, fg='cyan')


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
        self._traverse_group(self.test_suite)

        click.secho('\nRan %d tests in %ss.' % (
            self.successes + self.failures,
            round(time.time() - start_time, 2)
        ), bold=True)
        
        if self.failures > 0:
            click.echo('%d failed, %d passed (%d%% ok).' % (
                self.successes + self.failures, self.failures),
                100-round(self.failures/self.successes*100, 2))
            click.secho('\nfail.', fg='red')
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
        pad = self._max_length(tests) + 10

        self.failures = 0
        self.successes = 0

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
                display_pad(pad - test_name_length(test))
                if not len(issues):
                    self.successes += 1
                    click.secho(' PASSED', fg='green')
                else:
                    self.failures += 1
                    click.secho(' FAILED', fg='red')
                    for issue in issues:
                        click.secho(repr(issue.value), fg='cyan')
                        click.secho('  ' * len(test.id) +
                                    str(issue), fg='yellow')
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
