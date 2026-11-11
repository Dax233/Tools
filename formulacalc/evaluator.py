# SPDX-License-Identifier: AGPL-3.0-or-later
"""只对 AST 白名单节点求值——本模块里没有 eval / exec / compile。

安全模型：

* 解析器只会产出 Number/Constant/UnaryOp/BinaryOp/Function/Percent 六种节点；
* 求值器用 isinstance 逐类分发，认不出的节点直接报错；
* 函数表是写死的字典，不存在按名字去 globals() 里查函数这回事；
* 所有算术用标准库 math + Python 浮点，不 import numpy。

三角函数按**角度**（Word 课设场景），支持小数/负数角度。
"""

from __future__ import annotations

import math
from typing import Dict

from .errors import ExpressionError
from .parser import BinaryOp, Constant, Function, Node, Number, Percent, UnaryOp
from .symbols import Normalized

#: 指数绝对值上限，防止 9**9**9 这种把内存打爆的表达式。
MAX_ABS_EXPONENT = 1000.0

_CONSTANTS = {"pi": math.pi}  # type: Dict[str, float]

_TRIG = {"sin": math.sin, "cos": math.cos, "tan": math.tan}  # type: Dict[str, object]


def _error(normalized: Normalized, message: str, node: Node) -> ExpressionError:
    return normalized.error(message, getattr(node, "pos", 0))


def evaluate(node: Node, normalized: Normalized) -> float:
    """对 AST 求值；任何非有限结果（NaN/∞）都视为错误。"""

    value = _eval(node, normalized)
    if not isinstance(value, float):
        value = float(value)
    if not math.isfinite(value):
        raise _error(normalized, "结果不是有限数值（NaN 或无穷大）", node)
    return value


def _eval(node: Node, normalized: Normalized) -> float:
    if isinstance(node, Number):
        return float(node.value)

    if isinstance(node, Constant):
        value = _CONSTANTS.get(node.name)
        if value is None:  # pragma: no cover - 解析器只产出已知常量
            raise _error(normalized, "未知常量: {!r}".format(node.name), node)
        return value

    if isinstance(node, UnaryOp):
        operand = _eval(node.operand, normalized)
        if node.op == "-":
            return -operand
        return operand

    if isinstance(node, BinaryOp):
        left = _eval(node.left, normalized)
        right = _eval(node.right, normalized)
        if node.op == "+":
            return left + right
        if node.op == "-":
            return left - right
        if node.op == "*":
            return left * right
        if node.op == "/":
            if right == 0:
                raise _error(normalized, "除以零", node)
            return left / right
        if node.op == "**":
            return _power(left, right, node, normalized)
        raise _error(normalized, "不支持的运算符: {!r}".format(node.op), node)

    if isinstance(node, Function):
        argument = _eval(node.arg, normalized)
        if node.name in _TRIG:
            if not math.isfinite(argument):
                raise _error(normalized, "三角函数的角度不是有限数值", node)
            func = _TRIG[node.name]
            try:
                return float(func(math.radians(argument)))
            except (ValueError, OverflowError):
                raise _error(normalized, "三角函数参数超出可计算范围", node)
        if node.name == "sqrt":
            if argument < 0:
                raise _error(normalized, "√ 不能对负数开平方", node)
            return math.sqrt(argument)
        if node.name == "root4":
            if argument < 0:
                raise _error(normalized, "∜ 不能对负数开四次方", node)
            return math.pow(argument, 0.25)
        raise _error(normalized, "不支持的函数: {!r}".format(node.name), node)

    if isinstance(node, Percent):
        return _eval(node.operand, normalized) / 100.0

    raise _error(normalized, "不支持的语法结构，已拒绝求值", node)


def _power(base: float, exponent: float, node: Node, normalized: Normalized) -> float:
    if not math.isfinite(exponent):
        raise _error(normalized, "指数不是有限数值", node)
    if abs(exponent) > MAX_ABS_EXPONENT:
        raise _error(
            normalized,
            "指数过大（绝对值上限 {}），已拒绝计算".format(MAX_ABS_EXPONENT),
            node,
        )
    if base == 0 and exponent < 0:
        raise _error(normalized, "除以零（0 的负数次幂）", node)
    try:
        return math.pow(base, exponent)
    except OverflowError:
        raise _error(normalized, "数值上溢，结果超出浮点数范围", node)
    except ValueError:
        raise _error(normalized, "乘方定义域错误（负数的非整数次幂不是实数）", node)
