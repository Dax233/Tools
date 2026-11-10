# SPDX-License-Identifier: AGPL-3.0-or-later
"""CLI：退出码、stdout/stderr 分流、stdin 管道、剪贴板行为。"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from formulacalc import cli

ROOT = Path(__file__).resolve().parents[1]


def run_cli(*args, stdin=""):
    return subprocess.run(
        [sys.executable, "-m", "formulacalc", *args],
        cwd=str(ROOT),
        input=stdin,
        capture_output=True,
        text=True,
        timeout=30,
    )


def test_cli_expression_success():
    proc = run_cli("1+1")
    assert proc.returncode == 0
    assert proc.stdout.strip() == "2"
    assert proc.stderr == ""


def test_cli_trig_has_clean_stdout():
    proc = run_cli('"cos" 60^∘')
    assert proc.returncode == 0
    assert proc.stdout.strip() == "0.5"
    assert proc.stderr == ""


def test_cli_reads_stdin():
    proc = run_cli(stdin="2+3\n")
    assert proc.returncode == 0
    assert proc.stdout.strip() == "5"


def test_cli_multiline_paste():
    proc = run_cli(stdin="1 +\n2 +\n3\n")
    assert proc.returncode == 0
    assert proc.stdout.strip() == "6"


def test_cli_expression_error_exit_code():
    proc = run_cli("1/0")
    assert proc.returncode == 1
    assert proc.stdout == ""
    assert "错误" in proc.stderr


def test_cli_missing_input_exit_code():
    proc = run_cli(stdin="")
    assert proc.returncode == 2
    assert proc.stderr.strip() != ""


def test_cli_json_output():
    proc = run_cli("2*3", "--json")
    assert proc.returncode == 0
    payload = json.loads(proc.stdout)
    assert payload["result"] == 6.0
    assert payload["normalized"] == "2*3"


def test_cli_precision():
    proc = run_cli("1/3", "--precision", "2")
    assert proc.returncode == 0
    assert proc.stdout.strip() == "0.33"


def test_cli_debug_goes_to_stderr():
    proc = run_cli("2*3", "--debug")
    assert proc.returncode == 0
    assert proc.stdout.strip() == "6"
    assert "归一化" in proc.stderr


def test_cli_help():
    proc = run_cli("--help")
    assert proc.returncode == 0
    assert "formulacalc" in proc.stdout


def test_cli_version():
    proc = run_cli("--version")
    assert proc.returncode == 0
    assert "formulacalc" in proc.stdout


def test_legacy_wrapper_passthrough():
    proc = subprocess.run(
        [sys.executable, "bridgeDesign/wordFormulaCalculator.py", "1+1"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert proc.returncode == 0
    assert proc.stdout.strip() == "2"
    assert "formulacalc" in proc.stderr


def test_legacy_wrapper_forwards_errors():
    proc = subprocess.run(
        [sys.executable, "bridgeDesign/wordFormulaCalculator.py", "1/0"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert proc.returncode == 1
    assert "错误" in proc.stderr


# ---------------------------------------------------------------------------
# 剪贴板：默认不碰，只有显式 flag 才读/写
# ---------------------------------------------------------------------------


class FakeClipboard:
    def __init__(self, pasted="2+3"):
        self.copied = []
        self._pasted = pasted

    def copy(self, text):
        self.copied.append(text)

    def paste(self):
        return self._pasted


def test_clipboard_not_touched_by_default(monkeypatch):
    fake = FakeClipboard()
    monkeypatch.setitem(sys.modules, "pyperclip", fake)
    assert cli.main(["1+2"]) == 0
    assert fake.copied == []


def test_copy_flag_writes_clipboard(monkeypatch, capsys):
    fake = FakeClipboard()
    monkeypatch.setitem(sys.modules, "pyperclip", fake)
    assert cli.main(["--copy", "1+2"]) == 0
    assert fake.copied == ["3"]
    assert capsys.readouterr().out.strip() == "3"


def test_clipboard_read(monkeypatch, capsys):
    fake = FakeClipboard(pasted="2+3")
    monkeypatch.setitem(sys.modules, "pyperclip", fake)
    assert cli.main(["--clipboard"]) == 0
    assert capsys.readouterr().out.strip() == "5"


def test_clipboard_missing_dependency(monkeypatch, capsys):
    # sys.modules 里放 None，import pyperclip 会直接抛 ImportError。
    monkeypatch.setitem(sys.modules, "pyperclip", None)
    assert cli.main(["--copy", "1+2"]) == 2
    captured = capsys.readouterr()
    assert "pyperclip" in captured.err


def test_expression_and_clipboard_conflict():
    with pytest.raises(SystemExit) as info:
        cli.main(["1+1", "--clipboard"])
    assert info.value.code == 2


def test_negative_precision_usage_error():
    with pytest.raises(SystemExit) as info:
        cli.main(["1+1", "--precision", "-1"])
    assert info.value.code == 2
