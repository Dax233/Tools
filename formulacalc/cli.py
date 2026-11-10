# SPDX-License-Identifier: AGPL-3.0-or-later
"""命令行入口：formulacalc / python -m formulacalc。

退出码约定：

=====  ============================================================
0      计算成功
1      表达式解析 / 求值错误（ExpressionError）
2      用法或输入错误（缺少输入、--clipboard 不可用、参数冲突……）
=====  ============================================================
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import List, Optional

from . import ExpressionError, __version__, _evaluate_expression, _round_result


class _InputError(Exception):
    """输入阶段的问题（stdin / 剪贴板 / 参数），对应退出码 2。"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="formulacalc",
        description="把 Word/UnicodeMath 线性公式安全地算成数（不执行任何 Python 代码）。",
    )
    parser.add_argument(
        "expression",
        nargs="?",
        help="要计算的表达式；省略时从 stdin 读取（支持管道与多行粘贴）",
    )
    parser.add_argument(
        "--clipboard",
        action="store_true",
        help="从系统剪贴板读取表达式（需要可选依赖 pyperclip）",
    )
    parser.add_argument(
        "--copy",
        action="store_true",
        help="把结果写回系统剪贴板（需要可选依赖 pyperclip；默认不碰剪贴板）",
    )
    parser.add_argument(
        "--precision",
        type=int,
        default=4,
        metavar="N",
        help="结果保留的小数位数（默认 4）",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="把归一化后的表达式打印到 stderr",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="用 JSON 输出结果",
    )
    parser.add_argument("--version", action="version", version="formulacalc {}".format(__version__))
    return parser


def _load_pyperclip():  # type: ignore[no-untyped-def]
    try:
        import pyperclip  # type: ignore
    except ImportError:
        raise _InputError(
            "剪贴板功能需要可选依赖 pyperclip，请先安装：pip install 'formulacalc[clip]'"
            "（Linux 上还需要 xclip/xsel 等后端）"
        )
    return pyperclip


def _read_expression(args: argparse.Namespace) -> str:
    if args.clipboard:
        clipboard = _load_pyperclip()
        try:
            text = clipboard.paste()
        except Exception as exc:  # pyperclip 后端可能抛任何东西
            raise _InputError("读取剪贴板失败: {}（Linux 需要 xclip/xsel 等后端）".format(exc))
    elif args.expression is not None:
        text = args.expression
    else:
        text = sys.stdin.read()

    if text is None or not text.strip():
        raise _InputError("没有输入表达式（可用参数、stdin 或 --clipboard）")
    return text


def _format_number(value: float, precision: int) -> str:
    """整数结果不带小数点；小数按 precision 位输出并去掉多余的 0。"""

    if value == 0:
        value = 0.0
    if float(value).is_integer() and abs(value) < 1e16:
        return str(int(value))
    if precision > 0:
        text = "{:.{}f}".format(value, precision)
        if "." in text:
            text = text.rstrip("0").rstrip(".")
        return text or "0"
    return "{:g}".format(value)


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.precision < 0:
        parser.error("--precision 必须是非负整数")
    if args.expression is not None and args.clipboard:
        parser.error("不能同时给出表达式参数和 --clipboard")

    try:
        raw = _read_expression(args)
    except _InputError as exc:
        print("错误: {}".format(exc), file=sys.stderr)
        return 2

    try:
        normalized, value = _evaluate_expression(raw)
    except ExpressionError as exc:
        print("错误: {}".format(exc), file=sys.stderr)
        return 1

    if args.debug:
        print("归一化: {}".format(normalized.text), file=sys.stderr)

    result = _round_result(value, args.precision)

    if args.as_json:
        payload = {
            "expression": raw,
            "normalized": normalized.text,
            "result": result,
        }
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(_format_number(result, args.precision))

    if args.copy:
        try:
            clipboard = _load_pyperclip()
            clipboard.copy(_format_number(result, args.precision))
        except _InputError as exc:
            print("错误: {}".format(exc), file=sys.stderr)
            return 2
        except Exception as exc:  # 复制失败不应该假装成功
            print("错误: 写入剪贴板失败: {}".format(exc), file=sys.stderr)
            return 2

    return 0
