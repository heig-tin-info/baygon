from unittest import TestCase

from baygon.id import Id, TrackId


class TestId(TestCase):
    def test_id(self):
        i = Id("1.2.3.4")
        self.assertEqual(str(i), "1.2.3.4")
        self.assertEqual(tuple(i), (1, 2, 3, 4))
        self.assertEqual(list(i), [1, 2, 3, 4])

    def test_hash_and_pad(self):
        value = Id([1, 2])
        self.assertEqual(len(value), 2)
        self.assertEqual(value[1], 2)
        self.assertEqual(value.pad("."), ".")
        self.assertEqual(hash(value), hash(tuple(value)))

    def test_arithmetic_and_invalid_input(self):
        base = Id()
        incremented = base + 2
        self.assertEqual(str(incremented), "3")
        self.assertEqual(str(base.next()), "2")
        self.assertEqual(str(base.down(5)), "1.5")
        with self.assertRaises(ValueError):
            Id(object())

    def test_trackid(self):
        t = TrackId()
        t.down()
        self.assertEqual(str(t._id), "1")
        t.down()
        self.assertEqual(str(t._id), "1")
        u = t.down()(42)
        self.assertEqual(str(t._id), "1.1")
        self.assertEqual(u, 42)
        u = t.next()({})
        self.assertEqual(str(t._id), "1.2")
        self.assertEqual(u, {"test_id": [1, 1]})
        u = t.next()({})
        self.assertEqual(str(t._id), "1.3")
        self.assertEqual(u, {"test_id": [1, 2]})
        t.down()()
        self.assertEqual(str(t._id), "1.3.1")
        t.up()()
        self.assertEqual(str(t._id), "1.3")
        t.next()({})
        self.assertEqual(str(t._id), "1.4")
        t.down()()
        self.assertEqual(str(t._id), "1.4.1")
        t.reset()()
        self.assertEqual(str(t._id), "1")
