# SPDX-License-Identifier: AGPL-3.0-or-later
"""老脚本的"事故表"——每条都是实测过的行为，翻新后必须成立。"""

import math

import pytest

from formulacalc import calculate

# (表达式, 期望值)
ACCIDENT_TABLE = [
    ('"sin" 30^∘', 0.5),
    ('"sin" 30°', 0.5),
    ('"cos" 60^∘', 0.5),
    ('"tan" 45^∘', 1.0),
    ("√(9)", 3.0),
    ("√9", 3.0),
    ("∜(16)", 2.0),
    ("(1+2)^2", 9.0),
    ("3×4÷2", 6.0),
    ("50%", 0.5),
    ("2√(9)", 6.0),
    ("〖(3+4)〗×2", 14.0),
    ('"sin" 30^∘ + √(16)', 4.5),
]


@pytest.mark.parametrize("expression, expected", ACCIDENT_TABLE)
def test_accident_table(expression, expected):
    assert calculate(expression) == pytest.approx(expected, abs=1e-9)


@pytest.mark.parametrize(
    "expression, expected",
    [
        ('"sin" 30^∘', 0.5),
        ('"cos" 60^∘', 0.5),
        ('"tan" 45^∘', 1.0),
    ],
)
def test_trig_does_not_print_debug_noise(expression, expected, capsys):
    # 老脚本 cos/tan 分支复制粘贴了 print(np.sin(...))，终端里会多出一行。
    value = calculate(expression)
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""
    assert value == pytest.approx(expected)


def test_decimal_degree_angle():
    assert calculate('"sin" 30.5^∘', precision=10) == pytest.approx(
        math.sin(math.radians(30.5)), abs=1e-9
    )
    assert calculate('"sin" 30.5^∘', precision=6) == pytest.approx(0.507538, abs=1e-6)


def test_negative_angle():
    assert calculate('"sin" -30^∘') == pytest.approx(-0.5, abs=1e-9)


def test_undefined_variable_is_rejected_immediately():
    # 老脚本在这里 while 不收敛（死循环）。
    with pytest.raises(Exception):
        calculate('"sin" x')


def test_unclosed_sqrt_is_rejected_immediately():
    # 老脚本括号计数不归零，死循环。
    with pytest.raises(Exception):
        calculate("√(4")
