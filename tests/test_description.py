from unittest import TestCase

from baygon.suite import SuiteLoader


class TestDescription(TestCase):
    def setUp(self):
        self.loader = SuiteLoader()

    def get_sample(self, name="foobar"):
        return self.loader.load(
            data={
                "name": name,
                "version": 1,
                "tests": [{"exit": 0}],
            }
        )

    def test_build(self):
        name = "foobar"
        context = self.get_sample(name)
        self.assertEqual(context.name, name)
        self.assertEqual(context.version, 1)

    def test_len(self):
        context = self.get_sample("foobar")
        self.assertEqual(len(context.model.tests), 1)
