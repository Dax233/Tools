# SPDX-License-Identifier: AGPL-3.0-or-later
"""formulacalc —— 把 Word/UnicodeMath 线性公式安全地算成数。

用法::

    >>> from formulacalc import calculate
    >>> calculate('"sin" 30^∘')
    0.5
    >>> calculate('3×4÷2')
    6.0

设计要点：不调用 eval/exec/compile，只解析成 AST 后再按白名单求值，
所以 __import__("os").system(...) 这类输入在解析阶段就会被拒绝。
"""

from __future__ import annotations

from typing import Tuple

from .errors import ExpressionError
from .evaluator import evaluate
from .parser import parse
from .symbols import MAX_INPUT_LENGTH, Normalized, normalize

__version__ = "1.0.0"

__all__ = [
    "calculate",
    "ExpressionError",
    "normalize",
    "parse",
    "evaluate",
    "Normalized",
    "MAX_INPUT_LENGTH",
    "__version__",
]


def _evaluate_expression(expression: str) -> Tuple[Normalized, float]:
    """归一化 + 解析 + 求值，返回（归一化结果，原始数值）。

    这是给 CLI 和 calculate() 共用的内部管线，避免 --debug 时重复计算。
    """

    if not isinstance(expression, str):
        raise TypeError("expression 必须是 str，收到 {!r}".format(type(expression).__name__))
    normalized = normalize(expression)
    tree = parse(normalized)
    value = evaluate(tree, normalized)
    return normalized, value


def _round_result(value: float, precision: int) -> float:
    result = round(value, precision)
    if result == 0:  # 顺手把 -0.0 也归一成 0.0
        result = 0.0
    return float(result)


def calculate(expression: str, precision: int = 4) -> float:
    """计算表达式并四舍五入到 precision 位小数。

    :param expression: Word/UnicodeMath 风格的表达式文本。
    :param precision: 非负整数，默认 4（与旧脚本的 round(..., 4) 保持一致）。
    :raises ExpressionError: 表达式为空、含非法字符、超限、除零、域错误等。
    """

    if isinstance(precision, bool) or not isinstance(precision, int) or precision < 0:
        raise ValueError("precision 必须是非负整数")
    _, value = _evaluate_expression(expression)
    return _round_result(value, precision)
