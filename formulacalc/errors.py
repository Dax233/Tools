# SPDX-License-Identifier: AGPL-3.0-or-later
"""formulacalc 的异常类型。

这里只放"表达式有问题"这一种错误：用户输入不合法、超限、或者求值域出错，
全部统一成 ExpressionError，调用方只需要 catch 这一个类型。
"""

from __future__ import annotations

from typing import Optional


class ExpressionError(ValueError):
    """表达式无法被解析或求值时抛出。

    position 是**原文**（用户粘贴的那串字符）里的 0 基下标，
    source 是原始文本。两者一起用于把报错定位回粘贴的公式，
    而不是让人对着归一化后的 ASCII 版本发呆 (￣▽￣)"
    """

    def __init__(
        self,
        message: str,
        position: Optional[int] = None,
        source: Optional[str] = None,
    ) -> None:
        self.message = message
        self.position = position
        self.source = source
        super().__init__(message)

    def __str__(self) -> str:
        if self.position is None:
            return self.message
        text = "{}（位置 {}）".format(self.message, self.position + 1)
        if self.source and 0 <= self.position < len(self.source):
            start = max(0, self.position - 8)
            end = min(len(self.source), self.position + 8)
            snippet = self.source[start:end].replace("\n", " ").replace("\r", " ")
            text += "，附近: {!r}".format(snippet)
        return text

    def __repr__(self) -> str:
        return "ExpressionError({!r}, position={!r})".format(self.message, self.position)
