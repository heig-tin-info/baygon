from unittest import TestCase

from baygon.score import compute_points


class TestPoints(TestCase):
    def test_points_distribtion(self):
        for total_points in range(10, 1000, 30):
            s = {
                "version": 1,
                "points": total_points,
                "tests": [
                    {
                        "weight": 30,
                        "tests": [{"weight": 8}, {"weight": 10}, {"weight": 20}],
                    },
                    {
                        "weight": 20,
                        "tests": [{"weight": 500}, {"weight": 1000}, {"weight": 1000}],
                    },
                ],
            }
            compute_points(s)

            print(s)
            print(self.sum_points(s))
            self.assertEqual(self.sum_points(s), total_points)

    def test_points_distribtion_with_fixed_points(self):
        total_points = 50
        s = {
            "version": 1,
            "points": total_points,
            "tests": [
                {
                    "weight": 30,
                    "tests": [{"weight": 8}, {"weight": 10}, {"points": 2}],
                },
                {
                    "weight": 20,
                    "tests": [{"points": 3}, {"weight": 1000}, {"weight": 1000}],
                },
            ],
        }
        compute_points(s)

        print(s)
        print(self.sum_points(s))
        self.assertEqual(self.sum_points(s), total_points)

    def test_points_distribtion_unweighted(self):
        total_points = 60
        s = {
            "version": 1,
            "points": total_points,
            "tests": [
                {
                    "tests": [{}, {}, {}],
                },
                {
                    "tests": [{}, {}, {}],
                },
            ],
        }
        compute_points(s)

        print(s)
        print(self.sum_points(s))
        self.assertEqual(self.sum_points(s), total_points)

    def sum_points(self, data):
        """Recursively sum points key in data dictionary"""

        def sum_points(data):
            p = data.get("points", 0) if "tests" not in data else 0
            return p + sum(sum_points(t) for t in data.get("tests", []))

        return sum_points(data)
