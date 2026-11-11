# SPDX-License-Identifier: AGPL-3.0-or-later
"""UnicodeMath / Word 公式文本的归一化。

从 Word 里复制出来的线性公式（UnicodeMath）大概长这样::

    "sin" 30^∘ + √(16)

这里把它归一化成纯 ASCII 的记号序列::

    sin 30 + sqrt(16)

同时记录**每个归一化字符来自原文的哪个下标**（Normalized），
这样解析器报错时还能指回用户粘贴的那段文本。

归一化只做"字符级"的搬运，不改变语义：真正的解析交给 parser.py。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

from .errors import ExpressionError

#: 输入长度上限，防止有人把一整本小说粘进来（也顺带防 ReDoS/DoS）。
MAX_INPUT_LENGTH = 4096

#: 单字符 -> 替换字符串（1 对 1 或 1 对 N）。
_REPLACEMENTS = {
    "×": "*",
    "·": "*",  # 中间点乘号
    "⋅": "*",
    "✕": "*",
    "＊": "*",
    "÷": "/",
    "／": "/",
    "＋": "+",
    "－": "-",
    "−": "-",  # U+2212 数学减号
    "–": "-",
    "—": "-",
    "％": "%",
    "｛": "(",
    "｝": ")",
    "（": "(",
    "）": ")",
    "〖": "(",
    "〗": ")",
    "{": "(",
    "}": ")",
    "[": "(",
    "]": ")",
    "．": ".",
}

#: 这些字符在 Word 文本里是排版噪声，直接丢掉。
_DROPPED = set(
    '"“”„‟«»'  # 包住函数名的引号（旧脚本里 "sin" 的那对）
    "\\"  # 转义用的反斜杠
    "\u2061\u2062\u2063"  # 不可见的函数应用 / 乘号
    "∘°"  # 角度符号（旧脚本里 30^∘ 的 ∘ 与 30° 的 °）
)

#: 各种"看起来像空格"的 Unicode 空格统一成普通空格。
_SPACES = {"\u00a0": " ", "\u2009": " ", "\u202f": " ", "\u3000": " "}

#: 全角数字 -> 半角数字。
_FULLWIDTH_DIGITS = {chr(0xFF10 + i): str(i) for i in range(10)}

_REPLACEMENTS.update(_SPACES)
_REPLACEMENTS.update(_FULLWIDTH_DIGITS)


@dataclass(frozen=True)
class Normalized:
    """归一化结果：文本、原文下标映射、以及原文本身。"""

    text: str
    offsets: Tuple[int, ...]
    source: str

    def original_index(self, index: int) -> int:
        """把归一化文本里的下标换算回原文下标。"""

        if not self.offsets:
            return 0
        if index < 0:
            return 0
        if index >= len(self.offsets):
            return len(self.source)
        return self.offsets[index]

    def error(self, message: str, index: Optional[int] = None) -> ExpressionError:
        position = None if index is None else self.original_index(index)
        return ExpressionError(message, position=position, source=self.source)


def normalize(source: str) -> Normalized:
    """把 Word/UnicodeMath 文本归一化成 ASCII 记号序列。

    超过 MAX_INPUT_LENGTH 直接抛 ExpressionError，
    不进入任何逐字符循环之外的算法。
    """

    if not isinstance(source, str):
        raise TypeError("source 必须是 str，收到 {!r}".format(type(source).__name__))
    if len(source) > MAX_INPUT_LENGTH:
        raise ExpressionError(
            "表达式过长：{} 个字符超过上限 {}，已拒绝解析".format(len(source), MAX_INPUT_LENGTH),
            position=None,
            source=None,
        )

    out = []  # type: list
    offsets = []  # type: list
    index = 0
    length = len(source)

    def emit(piece: str, origin: int) -> None:
        for char in piece:
            out.append(char)
            offsets.append(origin)

    while index < length:
        char = source[index]

        # 旧脚本的 30^∘ / 30° 写法：^ 和角度符号成对出现，整体视作"角度标记"。
        # 三角函数默认就按角度算，所以这个标记归一化时直接丢掉。
        if char == "^":
            lookahead = index + 1
            while lookahead < length and source[lookahead].isspace():
                lookahead += 1
            if lookahead < length and source[lookahead] in "∘°":
                index = lookahead + 1
                continue
            emit("**", index)
            index += 1
            continue

        # 已经写成 **∘ 的形式（例如先做过一次 ^ -> ** 转换的文本）。
        if char == "*" and index + 1 < length and source[index + 1] == "*":
            lookahead = index + 2
            while lookahead < length and source[lookahead].isspace():
                lookahead += 1
            if lookahead < length and source[lookahead] in "∘°":
                index = lookahead + 1
                continue

        if char in "∘°":
            index += 1
            continue

        if char in _DROPPED:
            index += 1
            continue

        replacement = _REPLACEMENTS.get(char)
        if replacement is None:
            out.append(char)
            offsets.append(index)
        else:
            emit(replacement, index)
        index += 1

    return Normalized("".join(out), tuple(offsets), source)
