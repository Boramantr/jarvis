"""Paylaşılan JSON mtime cache yardımcısı.

memory/ altındaki tüm modüller buradan `load_json_cached(path, default_factory)`
çağırır. Dosya değişmediyse parse tekrarlanmaz — RAM + CPU + disk I/O tasarrufu.
"""
from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from threading import Lock
from typing import Any

_cache: dict[str, tuple[float, Any]] = {}
_lock = Lock()


def load_json_cached(path: str | Path, default_factory: Callable[[], Any] = dict) -> Any:
    p = Path(path)
    key = str(p)
    if not p.exists():
        return default_factory()
    with _lock:
        try:
            mtime = p.stat().st_mtime
            hit = _cache.get(key)
            if hit and hit[0] == mtime:
                return hit[1]
            data = json.loads(p.read_text(encoding="utf-8"))
            _cache[key] = (mtime, data)
            return data
        except Exception:
            return default_factory()


def invalidate(path: str | Path) -> None:
    """save_*() sonrası çağrılmalı — cache'i temizler."""
    with _lock:
        _cache.pop(str(Path(path)), None)


def clear_all() -> None:
    with _lock:
        _cache.clear()
