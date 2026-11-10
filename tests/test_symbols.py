# SPDX-License-Identifier: AGPL-3.0-or-later
"""归一化层：符号映射与原文位置回溯。"""

import pytest

from formulacalc import ExpressionError
from formulacalc.symbols import MAX_INPUT_LENGTH, normalize


def test_operator_normalization():
    assert normalize("1×2÷3−4").text == "1*2/3-4"


def test_word_degree_and_quotes():
    assert normalize('"sin" 30^∘').text == "sin 30"
    assert normalize('"sin" 30°').text == "sin 30"
    assert normalize('“cos” 60^∘').text == "cos 60"


def test_brackets_and_fullwidth():
    assert normalize("〖(3+4)〗×2").text == "((3+4))*2"
    assert normalize("（1＋2）").text == "(1+2)"
    assert normalize("{1+2}").text == "(1+2)"


def test_percent_and_power():
    assert normalize("50%").text == "50%"
    assert normalize("2^10").text == "2**10"


def test_positions_point_back_to_source():
    normalized = normalize("1 + @")
    index = normalized.text.index("@")
    assert normalized.original_index(index) == 4


def test_position_after_multi_char_replacement():
    # '^' 会被展开成 '**'，两个字符都应该指回原文的 '^'。
    normalized = normalize("2^10")
    first = normalized.text.index("*")
    assert normalized.original_index(first) == 1
    assert normalized.original_index(first + 1) == 1


def test_too_long_input_rejected():
    source = "1" * (MAX_INPUT_LENGTH + 1)
    with pytest.raises(ExpressionError) as info:
        normalize(source)
    assert str(MAX_INPUT_LENGTH) in str(info.value)
