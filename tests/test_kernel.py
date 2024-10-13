from pytest import fixture

from baygon.kernel import RestrictedEvaluator


@fixture
def repl():
    return RestrictedEvaluator()


def test_restricted_evaluator(repl):
    assert repl("a = 42") == 42
    assert repl("a + 2") == 44
    assert repl("a * 10") == 420
    assert repl.error is None
    assert repl("b + 2") is None
    assert repl.error is not None


def test_trigonometric_functions(repl):
    assert repl("sin(0)") == 0
    assert repl("cos(0)") == 1
    assert repl("tan(0)") == 0


def test_logarithmic_functions(repl):
    assert repl("log(1)") == 0
    assert repl("log10(10)") == 1
    assert repl("log2(2)") == 1
