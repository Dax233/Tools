# SPDX-License-Identifier: AGPL-3.0-or-later
"""安全回归：源码无 eval/exec、无第三方依赖、注入不执行、不死循环。"""

import ast
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PACKAGE_FILES = sorted((ROOT / "formulacalc").glob("*.py"))
WRAPPER = ROOT / "bridgeDesign" / "wordFormulaCalculator.py"


def test_package_sources_exist():
    assert PACKAGE_FILES
    assert WRAPPER.is_file()


@pytest.mark.parametrize("path", PACKAGE_FILES, ids=lambda p: p.name)
def test_no_eval_or_exec_calls(path):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"eval", "exec"}, "{} 里出现了 {} 调用".format(
                path.name, node.func.id
            )


@pytest.mark.parametrize("path", PACKAGE_FILES, ids=lambda p: p.name)
def test_no_eval_exec_identifier_anywhere(path):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            assert node.id not in {"eval", "exec"}
        elif isinstance(node, ast.Attribute):
            assert node.attr not in {"eval", "exec"}


def test_wrapper_has_no_eval_exec():
    tree = ast.parse(WRAPPER.read_text(encoding="utf-8"), filename=str(WRAPPER))
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"eval", "exec"}


#: 唯一的例外：剪贴板是可选依赖，只在 --clipboard/--copy 时惰性 import。
_OPTIONAL_DEPENDENCIES = {"pyperclip"}


def test_no_third_party_imports():
    if not hasattr(sys, "stdlib_module_names"):  # pragma: no cover - Python 3.9
        pytest.skip("sys.stdlib_module_names 需要 Python 3.10+")
    stdlib = set(sys.stdlib_module_names) | _OPTIONAL_DEPENDENCIES
    for path in PACKAGE_FILES:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root = alias.name.split(".")[0]
                    assert root in stdlib, "{} 引入了非标准库依赖 {}".format(path.name, root)
            elif isinstance(node, ast.ImportFrom):
                if node.level:  # 包内相对导入
                    continue
                root = (node.module or "").split(".")[0]
                assert root in stdlib, "{} 引入了非标准库依赖 {}".format(path.name, root)


def test_injection_does_not_execute():
    expression = '__import__("os").system("echo PWNED_BY_FORMULA")'
    proc = subprocess.run(
        [sys.executable, "-m", "formulacalc", expression],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert proc.returncode == 1
    assert "PWNED" not in proc.stdout
    assert "PWNED" not in proc.stderr


def test_undefined_variable_does_not_hang():
    proc = subprocess.run(
        [sys.executable, "-m", "formulacalc", '"sin" x'],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert proc.returncode == 1


def test_unclosed_parenthesis_does_not_hang():
    proc = subprocess.run(
        [sys.executable, "-m", "formulacalc", "√(4"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert proc.returncode == 1


def test_import_without_third_party_packages():
    proc = subprocess.run(
        [sys.executable, "-c", "import formulacalc; print(formulacalc.calculate('1+1'))"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert proc.returncode == 0
    assert proc.stdout.strip() == "2.0"  # calculate() 统一返回 float
    assert proc.stderr == ""
