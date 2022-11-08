from unittest import TestCase

from baygon.suite import TestSuite


class TestDescription(TestCase):
    def get_sample(self, name='foobar'):
        return TestSuite({
            'name': name,
            'version': 1,
            'tests': [
                {'exit': 0}
            ]
        })

    def test_build(self):
        name = 'foobar'
        td = self.get_sample(name)
        self.assertEqual(td.name, name)
        self.assertEqual(td.version, 1)

    def test_len(self):
        name = 'foobar'
        td = self.get_sample(name)
        self.assertEqual(len(td), 1)
