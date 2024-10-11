from baygon.score import compute_points, distribute, float_or_int, has_weights_or_points


def sum_points(data):
    """Recursively sum points key in data dictionary"""

    def _sum_points(data):
        p = data.get("points", 0) if "tests" not in data else 0
        return p + sum(_sum_points(t) for t in data.get("tests", []))

    return _sum_points(data)


def test_points_distribution():
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
        print(sum_points(s))
        assert sum_points(s) == total_points


def test_points_distribution_with_fixed_points():
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
    print(sum_points(s))
    assert sum_points(s) == total_points


def test_points_distribution_unweighted():
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
    print(sum_points(s))
    assert sum_points(s) == total_points


def test_float_or_int():
    assert float_or_int(1.0) == 1  # Test for integer result
    assert float_or_int(1.1) == 1.1  # Test for float result
    assert float_or_int(42.0) == 42  # Should return integer
    assert float_or_int(42.5) == 42.5  # Should return float


def test_distribute():
    assert distribute([1, 2, 3, 4], 10, 0.001) == [1, 2, 3, 4]
    assert distribute([1, 1, 1, 1], 100, 0.01) == [25, 25, 25, 25]
    assert distribute([12.5, 19.7, 42.1, 8.9], 100, 0.2) == [15, 23.7, 50.6, 10.7]
    assert distribute([100, 100, 200, 200], 50, 1) == [8, 8, 17, 17]


def test_distribute_with_rounding():
    assert distribute([2, 3], 10, 0.5) == [4.0, 6.0]
    assert distribute([2, 3], 10, 1) == [4, 6]  # Rounding should lead to integer


def test_has_weights_or_points():
    assert has_weights_or_points({"weight": 10}) is True  # Test with weight present
    assert has_weights_or_points({"points": 20}) is True  # Test with points present
    assert has_weights_or_points({"tests": [{"weight": 10}]}) is True  # Subtest weight
    assert has_weights_or_points({"tests": [{"points": 20}]}) is True  # Subtest points
    assert (
        has_weights_or_points({"tests": [{"subtests": []}]}) is False
    )  # No weights or points


def test_assign_points():
    data = {
        "points": 100,
        "tests": [
            {
                "weight": 30,
                "tests": [
                    {"weight": 8},
                    {"weight": 10},
                    {"weight": 12},
                ],
            },
            {
                "weight": 70,
                "tests": [
                    {"weight": 30},
                    {"weight": 40},
                ],
            },
        ],
    }
    compute_points(data)

    # Verify points are correctly assigned based on weights
    assert data["tests"][0]["points"] == 30
    assert data["tests"][1]["points"] == 70

    # Subtests of the first test group
    assert data["tests"][0]["tests"][0]["points"] == 8
    assert data["tests"][0]["tests"][1]["points"] == 10
    assert data["tests"][0]["tests"][2]["points"] == 12

    # Subtests of the second test group
    assert data["tests"][1]["tests"][0]["points"] == 30
    assert data["tests"][1]["tests"][1]["points"] == 40


def test_compute_points_fixed_and_weighted():
    data = {
        "points": 100,
        "tests": [
            {"points": 30, "tests": [{"weight": 10}, {"points": 20}]},
            {"weight": 70, "tests": [{"weight": 30}, {"weight": 40}]},
        ],
    }
    compute_points(data)

    # First group has fixed points for subtest, other points should be calculated
    assert data["tests"][0]["points"] == 30
    assert data["tests"][0]["tests"][0]["points"] == 10  # Remaining points
    assert data["tests"][0]["tests"][1]["points"] == 20  # Fixed points

    # Second group should distribute points based on weight
    assert data["tests"][1]["points"] == 70
    assert data["tests"][1]["tests"][0]["points"] == 30
    assert data["tests"][1]["tests"][1]["points"] == 40


def test_compute_points_no_weights_or_points():
    data = {
        "tests": [
            {"tests": [{}]},  # No points, no weights
            {"tests": [{}]},  # No points, no weights
        ]
    }
    result = compute_points(data)
    assert result["compute-score"] is False  # Shouldn't compute score


def test_compute_points_default_weight():
    data = {
        "points": 100,
        "tests": [
            {"tests": [{}]},  # Default weight should be 10
            {"tests": [{}]},  # Default weight should be 10
        ],
    }
    compute_points(data)
    assert data["tests"][0]["points"] == 50  # Should be equally distributed
    assert data["tests"][1]["points"] == 50  # Should be equally distributed


def test_min_point_behavior():
    data = {
        "points": 50,
        "min-points": 5,
        "tests": [
            {"weight": 1, "tests": [{"weight": 1}, {"weight": 2}]},
            {"weight": 1, "tests": [{"weight": 1}, {"weight": 2}]},
        ],
    }
    compute_points(data)

    # Min-points should ensure that no subtest has fewer than 5 points
    assert data["tests"][0]["tests"][0]["points"] >= 5
    assert data["tests"][0]["tests"][1]["points"] >= 5


def test_distribute_rounding():
    assert distribute([1, 2], 10, 0.01) == [3.33, 6.67]
    assert distribute([1, 1, 1], 100, 1) == [33, 33, 34]
