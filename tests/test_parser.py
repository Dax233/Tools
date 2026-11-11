# SPDX-License-Identifier: AGPL-3.0-or-later
"""解析层：报错信息、位置回溯、超限保护、解析期拒绝注入。"""

import pytest

from formulacalc import ExpressionError, calculate
from formulacalc.symbols import MAX_INPUT_LENGTH, normalize


@pytest.mark.parametrize(
    "expression, fragment",
    [
        ('"sin" x', "未知的函数或变量"),
        ("√(4", "缺少右括号"),
        ("log(2)", "未知的函数或变量"),
        ("1 + @", "无法识别"),
        ("sin()", "表达式不完整"),
    ],
)
def test_parse_errors(expression, fragment):
    with pytest.raises(ExpressionError) as info:
        calculate(expression)
    assert fragment in str(info.value)


@pytest.mark.parametrize("expression", ["", "   ", "\n\t", "()"])
def test_empty_or_broken_input(expression):
    with pytest.raises(ExpressionError):
        calculate(expression)


def test_error_position_points_back_to_source():
    with pytest.raises(ExpressionError) as info:
        calculate("1 + @")
    assert info.value.position == 4
    assert "位置 5" in str(info.value)


def test_too_long_input_is_rejected():
    expression = "1+" * 3000 + "1"  # 6001 字符
    with pytest.raises(ExpressionError) as info:
        calculate(expression)
    assert "过长" in str(info.value)
    assert str(MAX_INPUT_LENGTH) in str(info.value)


def test_deep_parentheses_are_rejected():
    expression = "(" * 80 + "1" + ")" * 80
    with pytest.raises(ExpressionError) as info:
        calculate(expression)
    assert "嵌套过深" in str(info.value)


def test_deep_unary_chain_is_rejected():
    expression = "-" * 500 + "1"
    with pytest.raises(ExpressionError) as info:
        calculate(expression)
    assert "嵌套过深" in str(info.value)


def test_unknown_identifier_rejected_at_parse_stage():
    # 安全性关键：__import__ 在解析期就应该被拒绝，绝不能走到求值。
    normalized = normalize('__import__("os").system("echo PWNED_BY_FORMULA")')
    with pytest.raises(ExpressionError):
        calculate(normalized.source)


def test_expression_error_is_value_error():
    assert issubclass(ExpressionError, ValueError)
