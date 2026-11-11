# SPDX-License-Identifier: AGPL-3.0-or-later
"""Tokenizer + 递归下降解析器。

文法（优先级从低到高）::

    expression := term (('+' | '-') term)*
    term       := unary (('*' | '/') unary | <隐式乘法> unary)*
    unary      := ('+' | '-') unary | power
    power      := postfix ('**' unary)?          # 右结合
    postfix    := primary ('%')*
    primary    := number | constant | '(' expression ')'
                | '√' unary | '∜' unary
                | function ( '(' expression ')' | unary )

设计约束：

* 只用"看过就前进、前进不了就报错"的循环，绝不写可能不收敛的 while；
* 递归深度和输入长度都有硬上限（防 DoS）；
* 未知标识符（例如 __import__）在**解析阶段**就拒绝，永远走不到求值。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Union
import re

from .errors import ExpressionError
from .symbols import Normalized

#: 语法树最大嵌套深度（防止 4096 个左括号把栈打穿）。
MAX_PARSE_DEPTH = 64

_FUNCTIONS = frozenset({"sin", "cos", "tan", "sqrt", "root4"})
_CONSTANTS = frozenset({"pi"})
_START_OF_OPERAND = frozenset({"number", "lparen", "ident", "root", "root4", "const_pi"})

_NUMBER_RE = re.compile(r"(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?")


@dataclass(frozen=True)
class Token:
    kind: str
    text: str
    pos: int


# ---------------------------------------------------------------------------
# AST 节点（只允许下面这些类型出现，evaluator 也只认这些类型）
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Number:
    value: float
    pos: int


@dataclass(frozen=True)
class Constant:
    name: str
    pos: int


@dataclass(frozen=True)
class UnaryOp:
    op: str
    operand: "Node"
    pos: int


@dataclass(frozen=True)
class BinaryOp:
    op: str
    left: "Node"
    right: "Node"
    pos: int


@dataclass(frozen=True)
class Function:
    name: str
    arg: "Node"
    pos: int


@dataclass(frozen=True)
class Percent:
    operand: "Node"
    pos: int


Node = Union[Number, Constant, UnaryOp, BinaryOp, Function, Percent]


# ---------------------------------------------------------------------------
# Tokenizer
# ---------------------------------------------------------------------------


def tokenize(normalized: Normalized) -> List[Token]:
    """把归一化文本切成 token；遇到不认识的字符立刻报错。"""

    text = normalized.text
    tokens = []  # type: List[Token]
    index = 0
    length = len(text)

    while index < length:
        char = text[index]

        if char.isspace():
            index += 1
            continue

        if char.isdigit() or (char == "." and index + 1 < length and text[index + 1].isdigit()):
            match = _NUMBER_RE.match(text, index)
            if match is None:  # pragma: no cover - 正则能匹配上面的条件，防御性分支
                raise normalized.error("无法解析数字", index)
            tokens.append(Token("number", match.group(0), index))
            index = match.end()
            continue

        # π 也是 Unicode 字母，必须在 isalpha() 的标识符分支之前截胡。
        if char == "π":
            tokens.append(Token("const_pi", char, index))
            index += 1
            continue

        if char.isalpha() or char == "_":
            start = index
            while index < length and (text[index].isalnum() or text[index] == "_"):
                index += 1
            tokens.append(Token("ident", text[start:index], start))
            continue

        if char == "*" and index + 1 < length and text[index + 1] == "*":
            tokens.append(Token("pow", "**", index))
            index += 2
            continue
        if char in "+-*/":
            tokens.append(Token("op", char, index))
            index += 1
            continue
        if char == "(":
            tokens.append(Token("lparen", char, index))
            index += 1
            continue
        if char == ")":
            tokens.append(Token("rparen", char, index))
            index += 1
            continue
        if char == "%":
            tokens.append(Token("percent", char, index))
            index += 1
            continue
        if char == "√":
            tokens.append(Token("root", char, index))
            index += 1
            continue
        if char == "∜":
            tokens.append(Token("root4", char, index))
            index += 1
            continue

        raise normalized.error("无法识别的字符 {!r}".format(char), index)

    tokens.append(Token("eof", "", length))
    return tokens


# ---------------------------------------------------------------------------
# 递归下降解析器
# ---------------------------------------------------------------------------


class Parser:
    def __init__(self, normalized: Normalized) -> None:
        self._normalized = normalized
        self._tokens = tokenize(normalized)
        self._index = 0

    # -- token 小工具 -------------------------------------------------------

    def _peek(self) -> Token:
        return self._tokens[self._index]

    def _advance(self) -> Token:
        token = self._tokens[self._index]
        self._index += 1
        return token

    def _error(self, message: str, pos: int) -> ExpressionError:
        return self._normalized.error(message, pos)

    def _check_depth(self, depth: int) -> None:
        if depth > MAX_PARSE_DEPTH:
            raise self._error(
                "表达式嵌套过深（上限 {} 层）".format(MAX_PARSE_DEPTH),
                self._peek().pos,
            )

    def _expect(self, kind: str, message: str) -> Token:
        token = self._peek()
        if token.kind != kind:
            raise self._error(message, token.pos)
        return self._advance()

    # -- 语法规则 -----------------------------------------------------------

    def parse(self) -> Node:
        if self._peek().kind == "eof":
            raise self._error("表达式为空", 0)
        node = self._parse_expression(0)
        token = self._peek()
        if token.kind != "eof":
            raise self._error(
                "多余的记号 {!r}（表达式在此处应该已经结束）".format(token.text),
                token.pos,
            )
        return node

    def _parse_expression(self, depth: int) -> Node:
        self._check_depth(depth)
        node = self._parse_term(depth + 1)
        while True:
            token = self._peek()
            if token.kind == "op" and token.text in "+-":
                self._advance()
                right = self._parse_term(depth + 1)
                node = BinaryOp(token.text, node, right, token.pos)
            else:
                return node

    def _parse_term(self, depth: int) -> Node:
        self._check_depth(depth)
        node = self._parse_unary(depth + 1)
        while True:
            token = self._peek()
            if token.kind == "op" and token.text in "*/":
                self._advance()
                right = self._parse_unary(depth + 1)
                node = BinaryOp(token.text, node, right, token.pos)
                continue
            # 隐式乘法：2(3+4)、(1+2)(3+4)、2√9、2π、2sin(30) ……
            if token.kind in _START_OF_OPERAND:
                right = self._parse_unary(depth + 1)
                node = BinaryOp("*", node, right, token.pos)
                continue
            return node

    def _parse_unary(self, depth: int) -> Node:
        self._check_depth(depth)
        token = self._peek()
        if token.kind == "op" and token.text == "-":
            self._advance()
            return UnaryOp("-", self._parse_unary(depth + 1), token.pos)
        if token.kind == "op" and token.text == "+":
            self._advance()
            return self._parse_unary(depth + 1)
        return self._parse_power(depth + 1)

    def _parse_power(self, depth: int) -> Node:
        self._check_depth(depth)
        base = self._parse_postfix(depth + 1)
        token = self._peek()
        if token.kind == "pow":
            self._advance()
            exponent = self._parse_unary(depth + 1)  # 右结合，且允许 2^-3
            return BinaryOp("**", base, exponent, token.pos)
        return base

    def _parse_postfix(self, depth: int) -> Node:
        self._check_depth(depth)
        node = self._parse_primary(depth + 1)
        while True:
            token = self._peek()
            if token.kind == "percent":
                self._advance()
                node = Percent(node, token.pos)
                continue
            return node

    def _parse_primary(self, depth: int) -> Node:
        self._check_depth(depth)
        token = self._peek()

        if token.kind == "number":
            self._advance()
            return Number(float(token.text), token.pos)

        if token.kind == "lparen":
            self._advance()
            node = self._parse_expression(depth + 1)
            self._expect("rparen", "缺少右括号 ')'")
            return node

        if token.kind in ("root", "root4"):
            self._advance()
            name = "sqrt" if token.kind == "root" else "root4"
            return Function(name, self._parse_unary(depth + 1), token.pos)

        if token.kind == "const_pi":
            self._advance()
            return Constant("pi", token.pos)

        if token.kind == "ident":
            name = token.text.lower()
            self._advance()
            if name in _FUNCTIONS:
                if self._peek().kind == "lparen":
                    self._advance()
                    argument = self._parse_expression(depth + 1)
                    self._expect("rparen", "缺少右括号 ')'")
                    return Function(name, argument, token.pos)
                # 无括号写法："sin" 30 —— 参数取一个一元表达式，遇到 + - * / 就停。
                argument = self._parse_unary(depth + 1)
                return Function(name, argument, token.pos)
            if name in _CONSTANTS:
                return Constant(name, token.pos)
            raise self._error("未知的函数或变量: {!r}".format(token.text), token.pos)

        raise self._error("表达式不完整：这里需要数字、括号或函数", token.pos)


def parse(normalized: Normalized) -> Node:
    """解析归一化后的表达式，返回 AST。"""

    try:
        return Parser(normalized).parse()
    except RecursionError:  # 双保险：即使深度检查漏了也不要把解释器打挂
        raise ExpressionError("表达式嵌套过深，已拒绝解析", position=None, source=normalized.source)
