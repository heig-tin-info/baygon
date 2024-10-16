"""Helper functions used in `eval` filter.
These functions are injected into the kernel and made available from
the mustaches templates.

Examples:

    >>> reset()
    >>> iter()
    0
    >>> iter()
    1
    >>> iter()
    2
    >>> iter(100, 10)
    100
    >>> iter(100, 10)
    110
    >>> iter(ctx='foo')
    0
    >>> iter(ctx='foo')
    1
    >>> reset()
    >>> iter()
    0
    >>> iter(100, 10)
    100
"""
from .kernel import RestrictedEvaluator
import random
import re

_context = {}


def reset():
    """Reset the context."""
    _context.clear()

class ContextIterator:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    @property
    def has_ended(self):
        return self.get('ended', False)

def iter(start=0, end=1, step=1, ctx:ContextIterator=None):
    """Custom iterator for eval input filter."""
    if ctx is None:
        raise ValueError("Context is required")

    if (not ctx):
        ctx.update({
            'start': start,
            'end': end,
            'step': step,
            'value': start,
            'ended': False
        })
        return ctx['value']
    ctx['value'] += step
    if ctx['value'] >= ctx['end']:
        ctx['ended'] = True
    return ctx['value']

def random(min=0, max=100, n=1, ctx=None):
    """Return a random number between min and max."""
    if (not ctx):
        ctx.update({
            'min': min,
            'max': max,
            'n': n,
            'ended': False
        })
    ctx = (min, max, n, ctx)

    return random.randint(min, max)

class Kernel:
    def __init__(self, mustaches=(r'{{', r'}}'), preambles=[]):
        self._kernel = RestrictedEvaluator()
        self._pattern = re.compile(f"{mustaches[0]}(.*?){mustaches[1]}")
        for preamble in preambles:
            self._kernel(preamble)

    def eval(self, value: str) -> str:
        pos = 0
        ret = ""
        for match in self._pattern.finditer(value):
            ret += value[pos : match.start()]
            ret += str(self._kernel(match.group(1)))
            pos = match.end()
        ret += value[pos:]
        return ret
