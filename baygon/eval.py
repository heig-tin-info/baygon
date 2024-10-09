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

_context = {}


def reset():
    """Reset the context."""
    _context.clear()


def iter(start=0, step=1, ctx=None):
    """Custom iterator for eval input filter."""
    ctx = (start, step, ctx)
    _context[ctx] = _context.get(ctx, start - step) + step
    return _context[ctx]
