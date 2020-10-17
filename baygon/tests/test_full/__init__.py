import os
from unittest import TestCase

import baygon

dir_path = os.path.dirname(os.path.realpath(__file__))


class TestDemo(TestCase):
    def test_minimal(self):
        print(dir_path)
        t = baygon.Tests(path=dir_path)
        ts = baygon.TestSuite(t)
        issues = ts.run()
        print(issues)
