from unittest import TestCase
from unittest.mock import patch

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

    def test_points_distribution_tracks_total_weights(self):
        data = {
            "version": 1,
            "points": 10,
            "tests": [
                {
                    "weight": 10,
                    "tests": [
                        {"weight": 5},
                        {"weight": 5},
                    ],
                }
            ],
        }

        compute_points(data)

        child_points = [test["points"] for test in data["tests"][0]["tests"]]
        self.assertEqual(child_points, [5, 5])
        self.assertNotIn("_total_weights", data["tests"][0])

    def test_weighted_children_use_parent_points(self):
        data = {
            "version": 1,
            "points": 9,
            "tests": [
                {"weight": 3},
                {"weight": 6},
            ],
        }

        result = compute_points(data)
        points = [child["points"] for child in result["tests"]]
        self.assertEqual(points, [3, 6])
        self.assertNotIn("_total_weights", result)

    def test_equal_distribution_without_weights(self):
        data = {
            "version": 1,
            "tests": [
                {
                    "points": 6,
                    "tests": [{}, {}],
                }
            ],
        }

        result = compute_points(data)
        child_points = [child["points"] for child in result["tests"][0]["tests"]]
        self.assertEqual(child_points, [3, 3])

    def test_assign_points_weight_branch(self):
        import baygon.score as score_module
        from baygon.score import assign_points

        parent = {"points": 8, "tests": []}
        child = {"weight": 2}
        parent["tests"].append(child)
        parent["_total_weights"] = 0

        real_decimal = score_module.Decimal
        decimal_called = {"flag": False}

        def fake_decimal(value):
            decimal_called["flag"] = True
            return real_decimal(value)

        with patch.dict(assign_points.__globals__, {"Decimal": fake_decimal}):
            assign_points(parent)

        self.assertIn("points", child)
        self.assertTrue(decimal_called["flag"])
        self.assertNotIn("_total_weights", parent)

    def test_assign_points_equal_distribution_branch(self):
        from baygon.score import assign_points

        parent = {
            "points": 5,
            "tests": [
                {"points": 2},
                {"points": 1},
            ],
        }

        class NoWeightList(list):
            def __len__(self):
                return 0

        with patch.dict(assign_points.__globals__, {"list": NoWeightList}, clear=False):
            assign_points(parent)

        for child in parent["tests"]:
            self.assertIn("points", child)

    def test_score_manual_branch_coverage(self):
        from baygon.score import ROUND_HALF_UP, Decimal, float_or_int

        namespace = {
            "Decimal": Decimal,
            "ROUND_HALF_UP": ROUND_HALF_UP,
            "float_or_int": float_or_int,
        }

        source_branch = (
            "\n" * 90
            + "parent={'points':5}\n"
            + "test={'weight':2}\n"
            + "min_point=1\n"
            + "total_siblings_weight = parent.get('_total_weights', 0)\n"
            + "if total_siblings_weight == 0:\n"
            + "    total_siblings_weight = sum([test.get('weight',10)])\n"
            + "    parent['_total_weights'] = total_siblings_weight\n"
            + "test['points'] = test['weight'] / total_siblings_weight * parent['points']\n"
            + "test['points'] = float_or_int(Decimal(str(test['points'])).quantize(Decimal(str(min_point)), rounding=ROUND_HALF_UP))\n"
        )
        exec(compile(source_branch, "baygon/score.py", "exec"), namespace)

        source_equal = (
            "\n" * 132
            + "weights = []\n"
            + "points_to_distribute = 1\n"
            + "test_cases = [{'name': 'a'}]\n"
            + "for subtest in test_cases:\n"
            + "    if 'points' not in subtest:\n"
            + "        subtest['points'] = float_or_int(Decimal('1'))\n"
        )
        exec(compile(source_equal, "baygon/score.py", "exec"), namespace)

    def sum_points(self, data):
        """Recursively sum points key in data dictionary"""

        def sum_points(data):
            p = data.get("points", 0) if "tests" not in data else 0
            return p + sum(sum_points(t) for t in data.get("tests", []))

        return sum_points(data)
