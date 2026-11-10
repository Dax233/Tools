# SPDX-License-Identifier: AGPL-3.0-or-later
"""求值层：嵌套、常量、隐式乘法、百分比、精度与域错误。"""

import math

import pytest

from formulacalc import ExpressionError, calculate


def test_nested_square_roots():
    assert calculate("√(√(16))") == 2.0
    assert calculate("√(√(√(256)))") == 2.0


def test_fourth_roots():
    assert calculate("∜(16)") == 2.0
    # 数学上 ∜(∜(16)) = ∜2 ≈ 1.1892，这里按真值断言（不按笔误的 =2）。
    assert calculate("∜(∜(16))", precision=10) == pytest.approx(2 ** 0.25, abs=1e-9)


def test_nested_functions():
    expected = math.sin(math.radians(math.cos(math.radians(60))))
    assert calculate("sin(cos(60))", precision=12) == pytest.approx(expected, abs=1e-12)


def test_pi_constant():
    assert calculate("π", precision=12) == pytest.approx(math.pi, abs=1e-12)
    assert calculate("pi", precision=12) == pytest.approx(math.pi, abs=1e-12)
    assert calculate("2π", precision=12) == pytest.approx(2 * math.pi, abs=1e-12)


@pytest.mark.parametrize(
    "expression, expected",
    [
        ("2(3+4)", 14.0),
        ("(1+2)(3+4)", 21.0),
        ("2√9", 6.0),
        ("2π", 2 * math.pi),
        ("2sin(30)", 1.0),
        ("3(2)(2)", 12.0),
    ],
)
def test_implicit_multiplication(expression, expected):
    assert calculate(expression, precision=12) == pytest.approx(expected, abs=1e-12)


@pytest.mark.parametrize(
    "expression, expected",
    [
        ("50%", 0.5),
        ("200%*3", 6.0),
        ("(50+50)%", 1.0),
        ("-50%", -0.5),
        ("2*50%", 1.0),
    ],
)
def test_percent_suffix(expression, expected):
    assert calculate(expression) == pytest.approx(expected)


@pytest.mark.parametrize(
    "expression, expected",
    [
        ("2^10", 1024.0),
        ("-3^2", -9.0),
        ("(-3)^2", 9.0),
        ("2^-2", 0.25),
        ("2**10", 1024.0),
    ],
)
def test_power_and_unary(expression, expected):
    assert calculate(expression) == pytest.approx(expected)


def test_fullwidth_input():
    assert calculate("（1＋2）×3") == 9.0


@pytest.mark.parametrize(
    "expression",
    ["1/0", "0/0", "√(-1)", "∜(-16)", "1e9999", "1e308*10", "2^10000", "(-8)^0.5"],
)
def test_runtime_domain_errors(expression):
    with pytest.raises(ExpressionError):
        calculate(expression)


def test_default_precision_is_four():
    assert calculate("1/3") == 0.3333
    assert calculate("2/3") == 0.6667


def test_precision_argument():
    assert calculate("1/3", precision=2) == 0.33
    assert calculate("1/3", precision=10) == pytest.approx(0.3333333333)
    assert calculate("1/3", precision=0) == 0.0


def test_invalid_precision():
    with pytest.raises(ValueError):
        calculate("1+1", precision=-1)
    with pytest.raises(ValueError):
        calculate("1+1", precision=2.5)


def test_non_string_input():
    with pytest.raises(TypeError):
        calculate(123)  # type: ignore[arg-type]


def test_evaluation_writes_nothing(capsys):
    for expression in ['"cos" 60^∘', '"tan" 45^∘', "1/3", "√(16)"]:
        calculate(expression)
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""
