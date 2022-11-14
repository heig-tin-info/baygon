from unittest import TestCase

from baygon.suite import TestSuite


class TestEval(TestCase):
    def testEval(self):
        ts = TestSuite({
            'filters': {'trim': True},
            'eval': True,
            'tests': [
                {
                    'args': ['{{ i = 10 }}'],
                    'stdout': {
                        'equals': '{{ i }}'
                    },
                    'exit': 0,
                }
            ]
        }, executable='/bin/echo')
        self.assertEqual(ts.run(), [[]])

    def testAdd(self):
        ts = TestSuite({
            'filters': {'trim': True},
            'eval': True,
            'tests': [
                {
                    'stdin': '({{ i = 10 }} + {{ j = 10 }}) * 42',
                    'args': ['-e', 'print eval <STDIN>'],
                    'stdout': {
                        'equals': '{{ (i + j) * 42}}'
                    },
                    'exit': 0,
                }
            ]
        }, executable='/bin/perl')
        self.assertEqual(ts.run(), [[]])

    def testRandom(self):
        ts = TestSuite({
            'filters': {'trim': True},
            'eval': True,
            'tests': [
                {
                    'stdin': '({{ i = randint(10,1000) }} + {{ j = randint(1,10) }}) * 42',
                    'args': ['-e', 'print eval <STDIN>'],
                    'stdout': {
                        'equals': '{{ (i + j) * 42}}'
                    },
                    'exit': 0,
                }
            ]
        }, executable='/bin/perl')
        self.assertEqual(ts.run(), [[]])

    def testRepeat(self):
        ts = TestSuite({
            'filters': {'trim': True},
            'eval': True,

            'tests': [
                {
                    'repeat': 10,
                    'stdin': '({{ i = iter(0) }} + {{ j = iter(10) }}) * 42',
                    'args': ['-e', 'print eval <STDIN>'],
                    'stdout': {
                        'equals': '{{ (i + j) * 42 }}'
                    },
                    'exit': 0,
                }
            ]
        }, executable='/bin/perl')
        self.assertEqual(ts.run(), [[]])
