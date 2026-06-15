"""Canlı durum deposu — JARVIS'in iç durumunu web reaktörüne yansıtır.

Qt thread'i (UI sinyalleri) buraya yazar, uvicorn thread'i (websocket) okur.
Thread-safe, kilit korumalı, tek bir snapshot dict döndürür.

Akış:
    main.py  → set(...)  → _state
    dashboard websocket → snapshot() → tarayıcı reaktörü
"""
from __future__ import annotations

import threading
import time

_lock = threading.Lock()
_t0 = time.time()

_state = {
    "mode": "online",          # standby | online | listen | think | speak
    "mood": "nominal",         # metin etiketi
    "mood_rgb": [90, 185, 245],
    "audio": 0.0,              # 0..1 canlı ses seviyesi
    "load": 0.42,              # 0..1 çıkış göstergesi (tool yoğunluğu)
    "core_temp": 36.5,         # °C (gerçek CPU sıcaklığı bağlanabilir)
    "bond": 0,                 # bağ seviyesi
    "tool": "",                # o an çalışan araç
}


def set(**kwargs) -> None:
    with _lock:
        for k, v in kwargs.items():
            if k in _state and v is not None:
                _state[k] = v


def set_mode(mode: str) -> None:
    set(mode=mode)


def set_audio(level: float) -> None:
    # Çok sık çağrılır — kilidi kısa tut
    with _lock:
        _state["audio"] = max(0.0, min(1.5, float(level)))


def snapshot() -> dict:
    with _lock:
        s = dict(_state)
    s["uptime_h"] = round((time.time() - _t0) / 3600, 1)
    return s
