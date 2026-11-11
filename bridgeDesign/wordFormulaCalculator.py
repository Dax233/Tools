#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0-or-later
"""wordFormulaCalculator 的薄兼容壳。

旧版本（122 行：字符串 replace 链 + 裸 eval + 不收敛的 while 循环）已经删除，
真正的实现在仓库根目录的 formulacalc/ 包里。

保留这个文件只是为了让老习惯可以直接用：

    python bridgeDesign/wordFormulaCalculator.py '"sin" 30^∘'

等价于：

    python -m formulacalc '"sin" 30^∘'
"""

from __future__ import annotations

import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from formulacalc.cli import main  # noqa: E402  必须在 sys.path 调整之后导入


def _run() -> int:
    print(
        "[!] wordFormulaCalculator 已迁移到 formulacalc 包；"
        "用法: python -m formulacalc '表达式'（或安装后直接用 formulacalc 命令）",
        file=sys.stderr,
    )
    return main(sys.argv[1:])


if __name__ == "__main__":
    sys.exit(_run())
