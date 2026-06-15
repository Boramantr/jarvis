"""code_runner — JARVIS'in jenerik kod yürütme yetisi.

Önceden tanımlı bir tool yetmediğinde, model burada Python veya PowerShell
parçası yazar ve sonucu alır. "Yapamam" cevabı yerine çözüm üretmesini sağlar.

Güvenlik: Tam sandbox değil (kullanıcının kendi makinesi) ama şu korumalar var:
  - timeout + çıktı boyutu sınırı
  - Python kodu için AST denetimi: yıkıcı kalıpları (disk format, rmtree /,
    fork-bomb, rm -rf /, registry silme) reddeder
  - PowerShell/CMD için tehlikeli komut deseni denetimi
"""
from __future__ import annotations

import ast
import os
import re
import subprocess
import sys
import tempfile
import threading

_MAX_OUTPUT = 4000        # döndürülen stdout/stderr karakter limiti
_DEFAULT_TIMEOUT = 30     # saniye
_HARD_TIMEOUT = 120

_CREATE_NO_WINDOW = 0x08000000 if os.name == "nt" else 0

# PowerShell/CMD için tehlikeli desenler (case-insensitive)
_SHELL_DANGER = [
    r"\bformat\s+[a-z]:",          # disk format
    r"\brm\s+-rf\s+/",             # kök silme
    r"\bremove-item\b.*-recurse.*\b[a-z]:\\",  # tüm sürücü
    r"\bdel\s+/[fsq]+\s+[a-z]:\\", # sürücü silme
    r"reg\s+delete\s+hk",          # registry silme
    r"diskpart",                   # disk yönetimi
    r"cipher\s+/w",                # güvenli silme
    r":\(\)\s*\{.*\};",            # fork bomb
    r"shutdown\b",                 # kapatma (system_power kullanılmalı)
    r"mkfs\.",                     # filesystem oluşturma
]

# Python AST için yasak çağrı kalıpları (modül.fonksiyon)
_PY_DANGER_ATTRS = {
    ("shutil", "rmtree"),
    ("os", "removedirs"),
}
_PY_DANGER_NAMES = {"__import__"}


def _check_python_safety(code: str) -> str | None:
    """Python kodunu AST ile tara. Tehlikeli kalıp varsa hata mesajı döner."""
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return f"Python syntax hatası: {e.msg} (satır {e.lineno})"
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            # shutil.rmtree("/") gibi kök-hedefli yıkıcı çağrı
            if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
                pair = (func.value.id, func.attr)
                if pair in _PY_DANGER_ATTRS and node.args:
                    arg = node.args[0]
                    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                        target = arg.value.strip().rstrip("\\/")
                        # Kök veya sürücü kökü hedefliyse reddet
                        if target in ("", "/", "C:", "c:") or re.match(r"^[a-zA-Z]:$", target):
                            return f"Reddedildi: {pair[0]}.{pair[1]} kök dizini hedefliyor."
            if isinstance(func, ast.Name) and func.id in _PY_DANGER_NAMES:
                return f"Reddedildi: yasak çağrı {func.id}()"
    return None


def _check_shell_safety(code: str) -> str | None:
    low = code.lower()
    for pat in _SHELL_DANGER:
        if re.search(pat, low):
            return f"Reddedildi: tehlikeli komut deseni ({pat})."
    return None


def _truncate(text: str) -> str:
    if not text:
        return ""
    if len(text) <= _MAX_OUTPUT:
        return text
    head = text[: _MAX_OUTPUT - 200]
    tail = text[-200:]
    return f"{head}\n... [{len(text) - _MAX_OUTPUT} karakter kırpıldı] ...\n{tail}"


def _stream_subprocess(cmd, timeout: int, shell: bool, player=None) -> tuple[int, str, str]:
    """Subprocess'i başlatır, stdout/stderr'i satır satır okur.
    Uzun süren işlerde kullanıcıya UI üzerinden canlı progress gösterir.
    Final stdout/stderr/exit-code döner.
    """
    proc = subprocess.Popen(
        cmd,
        shell=shell,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        creationflags=_CREATE_NO_WINDOW,
        bufsize=1,  # line-buffered
    )

    out_buf: list[str] = []
    err_buf: list[str] = []

    def _drain(pipe, buf, label):
        try:
            for line in pipe:
                buf.append(line)
                if player is not None:
                    try:
                        player.write_log(f"[code_runner:{label}] {line.rstrip()[:200]}")
                    except Exception:
                        pass
        except Exception:
            pass

    t_out = threading.Thread(target=_drain, args=(proc.stdout, out_buf, "stdout"), daemon=True)
    t_err = threading.Thread(target=_drain, args=(proc.stderr, err_buf, "stderr"), daemon=True)
    t_out.start(); t_err.start()

    try:
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()
        t_out.join(timeout=1); t_err.join(timeout=1)
        raise

    t_out.join(timeout=2); t_err.join(timeout=2)
    return proc.returncode, "".join(out_buf), "".join(err_buf)


def _run_python(code: str, timeout: int, player=None) -> tuple[int, str, str]:
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, encoding="utf-8"
    ) as tmp:
        tmp.write(code)
        tmp_path = tmp.name
    try:
        return _stream_subprocess(
            [sys.executable, "-u", tmp_path], timeout, shell=False, player=player
        )
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


def _run_powershell(code: str, timeout: int, player=None) -> tuple[int, str, str]:
    return _stream_subprocess(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", code],
        timeout, shell=False, player=player,
    )


def _run_cmd(code: str, timeout: int, player=None) -> tuple[int, str, str]:
    return _stream_subprocess(code, timeout, shell=True, player=player)


def code_runner_action(parameters: dict | None = None, player=None) -> str:
    params = parameters or {}
    lang = (params.get("lang") or "python").strip().lower()
    code = params.get("code") or ""
    try:
        timeout = int(params.get("timeout") or _DEFAULT_TIMEOUT)
    except (TypeError, ValueError):
        timeout = _DEFAULT_TIMEOUT
    timeout = max(1, min(timeout, _HARD_TIMEOUT))

    if not code.strip():
        return "Hata: çalıştırılacak kod boş."

    # ── Güvenlik denetimi ──
    if lang in ("py", "python"):
        danger = _check_python_safety(code)
    else:
        danger = _check_shell_safety(code)
    if danger:
        return danger

    if player:
        try:
            player.write_log(f"[code_runner] {lang} ({len(code)} karakter)")
        except Exception:
            pass

    try:
        if lang in ("py", "python"):
            rc, out, err = _run_python(code, timeout, player=player)
        elif lang in ("ps", "powershell", "pwsh"):
            rc, out, err = _run_powershell(code, timeout, player=player)
        elif lang in ("cmd", "bat", "shell"):
            rc, out, err = _run_cmd(code, timeout, player=player)
        else:
            return f"Hata: bilinmeyen dil '{lang}'. Desteklenen: python, powershell, cmd."
    except subprocess.TimeoutExpired:
        return f"Hata: kod {timeout} saniye içinde bitmedi (timeout)."
    except FileNotFoundError as e:
        return f"Hata: yorumlayıcı bulunamadı ({e})."
    except Exception as e:
        return f"Hata: kod çalıştırılamadı ({type(e).__name__}: {e})."

    out = _truncate(out)
    err = _truncate(err)

    if rc == 0 and not err:
        return out.strip() or "Tamamlandı (çıktı yok)."
    parts = [f"exit_code={rc}"]
    if out:
        parts.append(f"stdout:\n{out}")
    if err:
        parts.append(f"stderr:\n{err}")
    return "\n".join(parts)
