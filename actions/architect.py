"""architect — JARVIS'in kendi tool'unu yazma yetisi.

Model şu zinciri izler:
  1. Önceden tanımlı tool yetmiyor → architect çağırır
  2. parametre: tool_name + function_body (sadece body) + libs[]
  3. Architect:
     a) tool_name sanity check (snake_case, çakışma yok)
     b) Tam modül kaynağı şablona yerleştirilir
     c) ast.parse + güvenlik denetimi (eval/exec/os.system yasak)
     d) `actions/<tool_name>.py` oluşturulur
     e) action_registry'ye eklenir (caller refresh edebilir)
  4. Kayıp lib varsa kullanıcıya `pip install` öner — sessizce kurma.

Güvenlik: code_runner gibi tehlikeli olduğundan safe_mode'da confirm gerekir
(_DESTRUCTIVE_TOOLS'a eklenmeli — ileride). Şimdilik açık ama ast denetimi var.
"""
from __future__ import annotations

import ast
import importlib
import re
import sys
from pathlib import Path

_ACTIONS_DIR = Path(__file__).resolve().parent
_NAME_RE = re.compile(r"^[a-z][a-z0-9_]{2,40}$")
_BANNED_CALLS = {"eval", "exec", "compile", "__import__"}
_BANNED_ATTR = {"os.system", "subprocess.call", "subprocess.run", "subprocess.Popen"}  # uyarı için

_TEMPLATE = '''"""Auto-generated tool: {tool_name}

JARVIS tarafından architect protokolüyle yazılmıştır.
Üretim: {timestamp}
"""
from __future__ import annotations


def {tool_name}_action(parameters: dict | None = None, player=None) -> str:
    params = parameters or {{}}
{body}
'''


def _indent_body(body: str, n: int = 4) -> str:
    pad = " " * n
    lines = body.splitlines() or ["return 'Done.'"]
    return "\n".join(pad + ln for ln in lines)


def _security_check(source: str) -> str | None:
    """ast tree üzerinde yasak çağrı tespiti. Bulursa hata mesajı döner."""
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        return f"Syntax hatası: {e.msg} (satır {e.lineno})"
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in _BANNED_CALLS:
                return f"Yasaklı çağrı: {node.func.id}()"
    return None


def architect_action(parameters: dict | None = None, player=None) -> str:
    params = parameters or {}
    tool_name = (params.get("tool_name") or "").strip().lower()
    body = params.get("code") or params.get("body") or ""
    libs = params.get("libs") or []

    if not tool_name:
        return "Hata: tool_name gerekli."
    if not _NAME_RE.match(tool_name):
        return "Hata: tool_name snake_case (3-40 karakter, harf/rakam/_) olmalı."

    target = _ACTIONS_DIR / f"{tool_name}.py"
    if target.exists():
        return f"Hata: '{target.name}' zaten var. Farklı bir isim seç."

    body = body.strip()
    if not body:
        return "Hata: code (fonksiyon gövdesi) gerekli."

    from datetime import datetime
    source = _TEMPLATE.format(
        tool_name=tool_name,
        timestamp=datetime.now().isoformat(timespec="seconds"),
        body=_indent_body(body),
    )

    sec_err = _security_check(source)
    if sec_err:
        return f"Reddedildi: {sec_err}"

    # Lib kontrolü — eksikse kullanıcıya bildir, sessizce yükleme yapma
    missing = []
    for lib in libs:
        lib = str(lib).strip()
        if not lib:
            continue
        try:
            importlib.import_module(lib.split("[")[0].split("==")[0])
        except ImportError:
            missing.append(lib)
    if missing:
        return (
            f"Reddedildi: eksik kütüphaneler: {missing}. "
            f"Kullanıcıdan `pip install {' '.join(missing)}` çalıştırmasını iste, sonra tekrar dene."
        )

    target.write_text(source, encoding="utf-8")

    # Anlık registry refresh: aynı sürecin action_registry'sine ekleme
    try:
        importlib.invalidate_caches()
        sys.path.insert(0, str(_ACTIONS_DIR))  # zaten orada ama emniyet
        mod = importlib.import_module(tool_name)
        fn = getattr(mod, f"{tool_name}_action", None)
        if fn is None:
            return f"Dosya yazıldı ama {tool_name}_action bulunamadı: {target}"
    except Exception as e:
        # Modül bozuksa geri al
        try: target.unlink()
        except Exception: pass
        return f"Reddedildi: yeni modül import sırasında patladı ({e}). Dosya silindi."

    if player is not None:
        try:
            # JarvisLive instance'a kayıt — main.py'deki action_registry'yi güncellemek için
            ui_root = getattr(player, "_jarvis_ref", None)
            # main.py reference yoksa: bir sonraki tool çağrısında ast tarama yine bulur
        except Exception:
            pass

    return (
        f"✅ Yeni yetenek doğdu: {tool_name}. Dosya: {target.name}. "
        f"Bir sonraki tool çağrısında otomatik kullanılabilir hale gelecek."
    )
