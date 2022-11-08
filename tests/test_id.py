
from unittest import TestCase

from baygon.id import Id


class TestId(TestCase):
    def test_id(self):
        i = Id('1.2.3.4')
        self.assertEqual(str(i), '1.2.3.4')
        self.assertEqual(tuple(i), (1, 2, 3, 4))
        self.assertEqual(list(i), [1, 2, 3, 4])
