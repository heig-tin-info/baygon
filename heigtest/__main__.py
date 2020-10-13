import click
import time
from . import TestSuite, TestDescriptionList


@click.command()
@click.option('-v', '--verbose', count=True)
def run(verbose):
    """Run tests."""
    start_time = time.time()

    td = TestDescriptionList()
    ts = TestSuite(td)

    failures = []

    for t in ts:
        r = t.run()
        if not len(r):
            if (verbose == 0):
                click.echo(click.style('.', fg='green'), nl=False)
            elif (verbose > 1):
                click.echo('Test %d - %s' % (t.id, t.name), nl=False)
                click.echo(click.style('  PASSED', fg='green'))
        else:
            failures.append((t, r))
            if (verbose == 0):
                click.echo(click.style('x', fg='red'), nl=False)
            if (verbose > 1):
                display_failure(t, r)

    click.echo('\n')

    if (verbose == 0):
        for test, failure in failures:
            display_failure(test, failure)

    click.echo('\nRan %d tests found into %s, in %s.' % (
        len(ts),
        td.filename,
        round(time.time() - start_time, 2)
    ))

    if len(failures) > 0:
        click.echo('%d failed, %d passed (%d%%).' % (
            len(ts), len(failures),
            round(len(failures)/len(ts)*100, 2)))
        click.echo(click.style('\nfail.', fg='red'))
    else:
        click.echo(click.style('\nok.', fg='green'))


def display_failure(test, failures):
    click.echo('Test %d - %s' % (test.id, test.name), nl=False)
    click.echo(click.style('  FAILED', fg='red'))
    for f in failures:
        click.echo(click.style('  - ' + str(f), fg='yellow'))


if __name__ == '__main__':
    run()
