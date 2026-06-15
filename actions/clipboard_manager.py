"""
Clipboard Manager Action — Pano geçmişi yönetimi.
Kullanım: "3 önceki kopyaladığımı yapıştır", "Pano geçmişini göster", "Panoyu temizle"
"""
import json
import threading
from datetime import datetime
from pathlib import Path

try:
    import pyperclip
    _PYPERCLIP = True
except ImportError:
    _PYPERCLIP = False

_clipboard_history: list[dict] = []
_history_lock = threading.Lock()
_MAX_HISTORY = 30
_last_content = ""

HISTORY_FILE = Path.home() / ".jarvis" / "clipboard_history.json"


def _load_history():
    global _clipboard_history
    try:
        if HISTORY_FILE.exists():
            data = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
            if isinstance(data, list):
                _clipboard_history = data[-_MAX_HISTORY:]
    except Exception:
        _clipboard_history = []


def _save_history():
    try:
        HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        HISTORY_FILE.write_text(
            json.dumps(_clipboard_history[-_MAX_HISTORY:], ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
    except Exception:
        pass


def add_to_history(content: str):
    """Pano geçmişine yeni öğe ekle."""
    global _last_content
    if not content or not content.strip():
        return
    if content == _last_content:
        return

    _last_content = content
    entry = {
        "content": content[:500],
        "time": datetime.now().strftime("%H:%M:%S"),
        "date": datetime.now().strftime("%Y-%m-%d"),
    }

    with _history_lock:
        _clipboard_history.append(entry)
        if len(_clipboard_history) > _MAX_HISTORY:
            _clipboard_history.pop(0)
        _save_history()


def _monitor_clipboard():
    """Arka planda panoyu izleyen thread."""
    global _last_content
    import time

    while True:
        try:
            if _PYPERCLIP:
                current = pyperclip.paste()
                if current and current != _last_content:
                    add_to_history(current)
        except Exception:
            pass
        time.sleep(1.5)


def start_clipboard_monitor():
    """Clipboard monitor'ü arka planda başlat."""
    _load_history()
    t = threading.Thread(target=_monitor_clipboard, daemon=True, name="ClipboardMonitor")
    t.start()


def clipboard_manager_action(parameters: dict = None, player=None) -> str:
    params = parameters or {}
    action = params.get("action", "list")
    index = params.get("index", 1)

    if player:
        player.write_log(f"[Clipboard] Komut: {action}")

    if not _PYPERCLIP:
        return "pyperclip kütüphanesi yüklü değil. pip install pyperclip"

    _load_history()

    if action == "list":
        if not _clipboard_history:
            return "Pano geçmişi boş efendim."

        lines = ["📋 Pano Geçmişi (son 10):"]
        for i, entry in enumerate(reversed(_clipboard_history[:10]), 1):
            preview = entry["content"][:60].replace("\n", " ")
            lines.append(f"  {i}. [{entry['time']}] {preview}...")
        return "\n".join(lines)

    elif action in ("get", "paste", "recall"):
        try:
            idx = int(index)
        except (ValueError, TypeError):
            idx = 1

        if idx < 1 or idx > len(_clipboard_history):
            return f"Geçmişte {idx}. öğe bulunamadı. Toplam {len(_clipboard_history)} kayıt var."

        entry = _clipboard_history[-idx]
        content = entry["content"]
        pyperclip.copy(content)
        return f"Panoya kopyalandı: {content[:80]}..."

    elif action == "clear":
        with _history_lock:
            _clipboard_history.clear()
            _save_history()
        return "Pano geçmişi temizlendi efendim."

    elif action == "copy":
        text = params.get("text", "")
        if not text:
            return "Kopyalanacak metin belirtilmedi."
        pyperclip.copy(text)
        add_to_history(text)
        return f"Panoya kopyalandı: {text[:60]}"

    elif action == "search":
        query = params.get("query", "").lower()
        if not query:
            return "Aranacak terimi belirtin."
        results = [e for e in _clipboard_history if query in e["content"].lower()]
        if not results:
            return f"Pano geçmişinde '{query}' bulunamadı."
        lines = [f"🔍 '{query}' için {len(results)} sonuç:"]
        for e in results[-5:]:
            preview = e["content"][:60].replace("\n", " ")
            lines.append(f"  [{e['time']}] {preview}")
        return "\n".join(lines)

    return "Geçersiz pano komutu. Kullanılabilir: list, get, clear, copy, search"
