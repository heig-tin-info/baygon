""" Module used to compute the score of a test case.
  Used in academic.
"""

from decimal import ROUND_DOWN, ROUND_HALF_UP, Decimal, getcontext


def float_or_int(value):
    """Return a float or an integer.
    >>> float_or_int(1.0)
    1
    >>> float_or_int(1.1)
    1.1
    """
    if value == int(value):
        return int(value)
    return float(value)


def distribute(values, total, min_value):
    """Distrubute the values given using a minimum step to ensure
    the total sum is respected.

    >>> distribute([1, 2, 3, 4], 10, 0.001)
    [1, 2, 3, 4]
    >>> distribute([1, 1, 1, 1], 100, 0.01)
    [25, 25, 25, 25]
    >>> distribute([12.5, 19.7, 42.1, 8.9], 100, 0.2)
    [15, 23.7, 50.6, 10.7]
    >>> distribute([100, 100, 200, 200], 50, 1)
    [8, 8, 17, 17]
    """
    getcontext().prec = 28
    total_weight = sum(values)
    total = Decimal(str(total))
    min_value = Decimal(str(min_value))
    decimal_values = [Decimal(str(v)) for v in values]
    allocations = [v / Decimal(str(total_weight)) * total for v in decimal_values]

    # Round down to the nearest multiple of min_value
    quantizer = min_value
    allocations_rounded = [
        a.quantize(quantizer, rounding=ROUND_HALF_UP) for a in allocations
    ]

    # Adjust the allocations to match the total
    total_allocated = sum(allocations_rounded)
    difference = total - total_allocated

    # If the difference is not zero, adjust the allocations
    if difference != Decimal("0"):
        # Compute the number of units to adjust
        units_to_adjust = int(
            (difference / min_value).to_integral_value(rounding=ROUND_HALF_UP)
        )
        # Sort the allocations by their remainders
        remainders = [
            a - a.quantize(quantizer, rounding=ROUND_DOWN) for a in allocations
        ]
        if units_to_adjust > 0:
            indices = sorted(
                range(len(values)), key=lambda i: remainders[i], reverse=True
            )
            adjustment = min_value
        else:
            indices = sorted(range(len(values)), key=lambda i: remainders[i])
            adjustment = -min_value
            units_to_adjust = abs(units_to_adjust)

        for i in range(units_to_adjust):
            idx = indices[i % len(indices)]
            allocations_rounded[idx] += adjustment

    return [float_or_int(a) for a in allocations_rounded]


def assign_points(test, parent=None):  # noqa: C901
    """Assign points recursively to each test in the structure."""
    min_point = test.get("min-points", parent.get("min-points", 1) if parent else 1)

    # Case 6: Default points if there are weights or points somewhere
    default_point = 1 if has_weights_or_points(test) else 0

    # Set default weight to 10 if not specified
    if "weight" not in test and "points" not in test and "tests" in test:
        test["weight"] = 10

    # If 'points' is not in test, compute it based on parent's points and weights
    if "points" not in test:
        if "weight" in test and parent and "points" in parent:
            total_siblings_weight = parent.get("_total_weights", 0)
            if total_siblings_weight == 0:
                total_siblings_weight = sum(
                    t.get("weight", 10) for t in parent.get("tests", [])
                )
                parent["_total_weights"] = total_siblings_weight
            test["points"] = test["weight"] / total_siblings_weight * parent["points"]
            test["points"] = float_or_int(
                Decimal(str(test["points"])).quantize(
                    Decimal(str(min_point)), rounding=ROUND_HALF_UP
                )
            )
        else:
            test["points"] = default_point

    # If there are subtests, assign points to them
    if "tests" in test:
        fixed_points = sum(
            subtest.get("points", 0) for subtest in test["tests"] if "points" in subtest
        )
        weights = []
        subtests_to_distribute = []
        for subtest in test["tests"]:
            if "points" in subtest:
                continue  # Skip subtests that already have points
            elif "weight" in subtest:
                weights.append(subtest["weight"])
                subtests_to_distribute.append(subtest)
            else:
                # Case 2 and 6: Default weight is 10 if not specified
                subtest["weight"] = 10
                weights.append(subtest["weight"])
                subtests_to_distribute.append(subtest)

        points_to_distribute = test["points"] - fixed_points

        if weights and points_to_distribute > 0:
            allocated_points = distribute(weights, points_to_distribute, min_point)
            for subtest, points in zip(subtests_to_distribute, allocated_points):
                subtest["points"] = points
        elif not weights and points_to_distribute > 0:
            # Case 3: No weights but points are given to all tests
            equally_divided_point = points_to_distribute / len(test["tests"])
            for subtest in test["tests"]:
                if "points" not in subtest:
                    subtest["points"] = float_or_int(
                        Decimal(str(equally_divided_point)).quantize(
                            Decimal(str(min_point)), rounding=ROUND_HALF_UP
                        )
                    )

    # Recursive call for subtests
    if "tests" in test:
        for subtest in test["tests"]:
            assign_points(subtest, parent=test)

    # Clean up temporary keys
    if "_total_weights" in test:
        del test["_total_weights"]


def has_weights_or_points(test):
    """Check if there are weights or points in the test or its subtests.
    >>> has_weights_or_points({"weight": 10})
    True
    """
    if "weight" in test or "points" in test:
        return True
    if "tests" in test:
        return any(has_weights_or_points(subtest) for subtest in test["tests"])
    return False


def compute_points(data):
    """Compute points for the entire structure."""
    # Case 4: If no weights or points exist anywhere, do nothing
    if not has_weights_or_points(data):
        data["compute-score"] = False
        return data

    # Case 5: Set compute-score to true
    data["compute-score"] = True

    # Case 7: If total points are given at root but no other info, set default weight
    if "points" in data and "tests" in data:
        for test in data["tests"]:
            if "weight" not in test and "points" not in test:
                test["weight"] = 10

    assign_points(data)
    return data
