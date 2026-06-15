"""Architect (self-coding) güvenlik testleri."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "actions"))

from architect import _NAME_RE, _indent_body, _security_check  # noqa: E402


def test_blocks_exec():
    err = _security_check("def f():\n    exec('x=1')")
    assert err and "exec" in err


def test_blocks_eval():
    err = _security_check("def f():\n    eval('1+1')")
    assert err and "eval" in err


def test_allows_clean_code():
    src = "def my_tool_action(parameters=None, player=None):\n    return 'ok'"
    assert _security_check(src) is None


def test_syntax_error_caught():
    err = _security_check("def f(:\n  pass")
    assert err and "Syntax" in err


def test_name_validation():
    assert _NAME_RE.match("weather_v2")
    assert not _NAME_RE.match("Weather")    # büyük harf
    assert not _NAME_RE.match("ab")          # çok kısa
    assert not _NAME_RE.match("my-tool")     # tire


def test_indent_body():
    out = _indent_body("return 1", n=4)
    assert out == "    return 1"
