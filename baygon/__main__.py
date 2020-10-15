import click
import time
import json
import logging
import os

from . import TestSuite, TestDescriptionList

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
    display_test_name(test)
    display_pad(pad - len(test.name) - len(str(test.id)))
    click.secho(' PASSED', fg='green')

def display_fail(test, pad=0):
    display_test_name(test)
    display_pad(pad - len(test.name) - len(str(test.id)))
    click.secho(' FAILED', fg='red')

def display_test_name(test):
    click.secho(f'Test {test.id}: ', nl=False, bold=True)
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

@click.command()
@click.argument('executable', required=False, type=click.Path(exists=True))
@click.option('-c', '--check', is_flag=True)
@click.option('-v', '--verbose', count=True)
@click.option('-l', '--limit', type=int, default=-1)
@click.option('--list', default=False, is_flag=True)
def cli(verbose=0, executable=None, **kwargs):
    """Run tests."""

    if 'check' in kwargs and kwargs['check']:
        td = TestDescriptionList(executable=executable)
        # try:
        #     td = TestDescriptionList(executable=executable)
        # except:
        #     click.secho("Error", fg='red')
        #     exit(1)
        # click.secho("Good", fg='green')
        exit(0)

    if verbose > 3:
        handler = logging.StreamHandler()
        formatter = OneLineExceptionFormatter(logging.BASIC_FORMAT)
        handler.setFormatter(formatter)
        root = logging.getLogger()
        root.setLevel(os.environ.get("LOGLEVEL", "DEBUG"))
        root.addHandler(handler)

    start_time = time.time()

    td = TestDescriptionList(executable=executable)

    if ('list' in kwargs and kwargs['list']):
        print(td)
        exit(0)

    ts = TestSuite(td)

    failures = []

    pad = pad_size(ts)

    limit = kwargs['limit']

    for k, t in enumerate(ts):
        if (limit > 0 and k > limit): break

        r = t.run()
        if not len(r):
            if (verbose == 0):
                click.secho('.', fg='green', nl=False)
            elif (verbose >= 1):
                display_pass(t, pad)
        else:
            failures.append((t, r))
            if (verbose == 0):
                click.secho('x', fg='red', nl=False)
            if (verbose >= 1):
                display_failure(t, r, pad, verbose=verbose)

    click.echo('\n')

    if (verbose == 0):
        for test, failure in failures:
            display_failure(test, failure, pad)

    click.secho('Ran %d tests in %ss.' % (
        len(ts),
        round(time.time() - start_time, 2)
    ), bold=True)

    if len(failures) > 0:
        click.echo('%d failed, %d passed (%d%% ok).' % (
            len(ts), len(failures),
            100-round(len(failures)/len(ts)*100, 2)))
        click.secho('\nfail.', fg='red')
    else:
        click.secho('\nok.', fg='green')

    exit(bool(len(failures)))


if __name__ == '__main__':
    cli()
