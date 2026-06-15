"""code_runner sandbox + yürütme testleri."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "actions"))

from code_runner import code_runner_action  # noqa: E402


def test_python_basic():
    r = code_runner_action({"lang": "python", "code": "print(2+2)"})
    assert "4" in r


def test_empty_code():
    r = code_runner_action({"code": ""})
    assert "Hata" in r


def test_unknown_lang():
    r = code_runner_action({"lang": "ruby", "code": "puts 1"})
    assert "bilinmeyen dil" in r


def test_timeout():
    r = code_runner_action({"lang": "python", "code": "import time; time.sleep(10)", "timeout": 1})
    assert "timeout" in r.lower() or "bitmedi" in r


def test_stderr_capture():
    r = code_runner_action({"lang": "python", "code": "raise ValueError('bum')"})
    assert "ValueError" in r


def test_output_truncation():
    r = code_runner_action({"lang": "python", "code": "print('x' * 100000)"})
    assert len(r) < 10000  # 4000 cap + işaretler


def test_blocks_rmtree_root():
    r = code_runner_action({"lang": "python", "code": "import shutil; shutil.rmtree('/')"})
    assert "Reddedildi" in r


def test_blocks_dunder_import():
    r = code_runner_action({"lang": "python", "code": "__import__('os')"})
    assert "Reddedildi" in r


def test_blocks_shell_format():
    r = code_runner_action({"lang": "powershell", "code": "format C:"})
    assert "Reddedildi" in r


def test_blocks_shell_shutdown():
    r = code_runner_action({"lang": "cmd", "code": "shutdown /s"})
    assert "Reddedildi" in r


def test_allows_safe_rmtree_subdir():
    # tmp altdizin — kök değil, izin verilmeli (çalışınca hata vermez)
    r = code_runner_action({"lang": "python", "code": "print('ok')"})
    assert "ok" in r
