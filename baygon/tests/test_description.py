from unittest import TestCase
from baygon.description import Tests


class TestDescription(TestCase):
    def getSample(self, name='foobar'):
        return Tests({
            'name': name,
            'version': 1,
            'tests': [
                {'exit': 0}
            ]
        })

    def test_build(self):
        name = 'foobar'
        td = self.getSample(name)
        self.assertEqual(td.name, name)
        self.assertEqual(td.version, 1)

    def test_len(self):
        name = 'foobar'
        td = self.getSample(name)
        self.assertEqual(len(td), 1)
