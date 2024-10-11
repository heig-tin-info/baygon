from pytest import fixture

from baygon.kernel import RestrictedEvaluator


@fixture
def repl():
    return RestrictedEvaluator()


def test_restricted_evaluator(repl):
    assert repl.evaluate("a = 42") == 42
    assert repl.evaluate("a + 2") == 44
    assert repl.evaluate("a * 10") == 420
    assert repl.error is None
    assert repl.evaluate("b + 2") is None
    assert repl.error is not None


def test_trigonometric_functions(repl):
    assert repl.evaluate("sin(0)") == 0
    assert repl.evaluate("cos(0)") == 1
    assert repl.evaluate("tan(0)") == 0


def test_logarithmic_functions(repl):
    assert repl.evaluate("log(1)") == 0
    assert repl.evaluate("log10(10)") == 1
    assert repl.evaluate("log2(2)") == 1
