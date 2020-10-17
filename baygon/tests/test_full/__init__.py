import os
from unittest import TestCase

import baygon

dir_path = os.path.dirname(os.path.realpath(__file__))


class TestDemo(TestCase):
    def test_minimal(self):
        print(dir_path)
        t = baygon.TestSuite(
            path=dir_path,
            executable=baygon.Executable(os.path.join(dir_path, 'main.py')))

        issues = t.run()
        print(issues)
