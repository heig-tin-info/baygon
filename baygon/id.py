""" Hierarchical Id class to identify nested sequences """
from typing import List
from collections.abc import Sequence
import re


class Id(Sequence):
    """ Test identifier. Helper class to number tests.

    Example:

    >>> i = Id()
    Id(1)
    >>> i = i.down()
    Id(1.1)
    >>> i += 1
    Id(1.2)
    >>> i += 2
    Id(1.4)
    >>> str(i)
    1.4
    >>> i.up()
    Id(1)
    >>> ((i + 1).down() + 1).down()
    Id(2.2.1)
    >>> tuple(Id().down().next().down().next().down().next())
    (1, 2, 2, 2)
    """

    def __init__(self, ids: List[int] = None):
        if isinstance(ids, int):
            ids = [ids]
        if isinstance(ids, Id):
            ids = ids.ids
        if isinstance(ids, str) and re.match(r'^\d+(\.\d+)*$', ids):
            ids = [int(i) for i in ids.split('.')]
        if ids is not None and not isinstance(ids, list):
            raise ValueError(f"Invalid type for Id: {type(ids)}")

        self.ids = ids or [1]

    def next(self):
        """ Return a new Id with the last id incremented. """
        return self + 1

    def down(self, base: int = 1):
        """ Return a new Id with the given id appended. """
        return Id(self.ids + [base])

    def up(self):
        """ Return a new Id with the given id appended. """
        return Id(self.ids[:-1])

    def __str__(self):
        return '.'.join([str(i) for i in self.ids])

    def __repr__(self):
        return f'Id({str(self)})'

    def __add__(self, other):
        return Id(self.ids[:-1] + [self.ids[-1] + other])

    def __list__(self):
        return self.ids

    def __iter__(self):
        for i in self.ids:
            yield i

    def __len__(self):
        return len(self.ids)

    def __hash__(self):
        return hash(tuple(self))

    def __getitem__(self, item):
        return self.ids[item]
