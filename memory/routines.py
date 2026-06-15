"""
Routines Tracker — Kullanıcının davranış kalıplarını ve rutinlerini öğrenir.
Uyku saati, çalışma saatleri, sık kullanılan uygulamalar vb.
"""
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from threading import Lock

from memory._jsoncache import invalidate as _invalidate
from memory._jsoncache import load_json_cached

ROUTINES_FILE = Path.home() / ".jarvis" / "memory" / "routines.json"
_lock = Lock()


def _load() -> dict:
    data = load_json_cached(ROUTINES_FILE, _empty)
    return data if isinstance(data, dict) else _empty()


def _empty() -> dict:
    return {
        "active_hours": [],         # Son 30 günün aktif saatleri
        "app_usage": {},            # Uygulama kullanım sayıları
        "command_usage": {},        # Komut kullanım sayıları
        "daily_first_seen": {},     # Günlük ilk aktif olma saati
        "daily_last_seen": {},      # Günlük son aktif olma saati
        "music_genres": {},         # Müzik türü tercihleri
        "work_sessions": [],        # Çalışma seansları
    }


def _save(data: dict):
    ROUTINES_FILE.parent.mkdir(parents=True, exist_ok=True)
    with _lock:
        ROUTINES_FILE.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        _invalidate(ROUTINES_FILE)


def track_activity():
    """Mevcut aktiviteyi kaydet (her etkileşimde çağrılır)."""
    data = _load()
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    hour = now.hour

    # Aktif saat kaydet
    data["active_hours"].append(hour)
    data["active_hours"] = data["active_hours"][-720:]  # Son 30 günlük (~24*30)

    # İlk/son görülme
    if today not in data["daily_first_seen"]:
        data["daily_first_seen"][today] = now.strftime("%H:%M")
    data["daily_last_seen"][today] = now.strftime("%H:%M")

    # Eski verileri temizle (30 günden fazla)
    cutoff_keys = sorted(data["daily_first_seen"].keys())
    if len(cutoff_keys) > 30:
        for old_key in cutoff_keys[:-30]:
            data["daily_first_seen"].pop(old_key, None)
            data["daily_last_seen"].pop(old_key, None)

    _save(data)


def track_app(app_name: str):
    """Uygulama kullanımını kaydet."""
    data = _load()
    key = app_name.lower().strip()
    data["app_usage"][key] = data["app_usage"].get(key, 0) + 1

    # En çok 50 uygulama tut
    if len(data["app_usage"]) > 50:
        sorted_apps = sorted(data["app_usage"].items(), key=lambda x: x[1], reverse=True)
        data["app_usage"] = dict(sorted_apps[:50])

    _save(data)


def track_command(command_name: str):
    """Komut kullanımını kaydet."""
    data = _load()
    data["command_usage"][command_name] = data["command_usage"].get(command_name, 0) + 1
    _save(data)


def track_work_session(duration_minutes: int):
    """Çalışma seansını kaydet."""
    data = _load()
    data["work_sessions"].append({
        "date": datetime.now().strftime("%Y-%m-%d"),
        "duration": duration_minutes,
        "ended": datetime.now().strftime("%H:%M"),
    })
    data["work_sessions"] = data["work_sessions"][-100:]  # Son 100 seans
    _save(data)


def get_patterns() -> dict:
    """Kullanıcı davranış kalıplarını analiz et."""
    data = _load()

    patterns = {}

    # En aktif saatler
    if data["active_hours"]:
        hour_counts = Counter(data["active_hours"])
        peak_hours = hour_counts.most_common(3)
        patterns["peak_hours"] = [h for h, _ in peak_hours]

    # Ortalama başlangıç/bitiş
    first_times = list(data["daily_first_seen"].values())
    last_times = list(data["daily_last_seen"].values())

    if first_times:
        avg_start_minutes = sum(
            int(t.split(":")[0]) * 60 + int(t.split(":")[1]) for t in first_times[-7:]
        ) / min(len(first_times), 7)
        patterns["avg_start"] = f"{int(avg_start_minutes // 60):02d}:{int(avg_start_minutes % 60):02d}"

    if last_times:
        avg_end_minutes = sum(
            int(t.split(":")[0]) * 60 + int(t.split(":")[1]) for t in last_times[-7:]
        ) / min(len(last_times), 7)
        patterns["avg_end"] = f"{int(avg_end_minutes // 60):02d}:{int(avg_end_minutes % 60):02d}"

    # En çok kullanılan uygulamalar
    if data["app_usage"]:
        top_apps = sorted(data["app_usage"].items(), key=lambda x: x[1], reverse=True)[:5]
        patterns["top_apps"] = top_apps

    # En çok kullanılan komutlar
    if data["command_usage"]:
        top_cmds = sorted(data["command_usage"].items(), key=lambda x: x[1], reverse=True)[:5]
        patterns["top_commands"] = top_cmds

    # Ortalama çalışma süresi
    sessions = data["work_sessions"]
    if sessions:
        recent = sessions[-10:]
        avg_duration = sum(s["duration"] for s in recent) / len(recent)
        patterns["avg_work_session"] = f"{int(avg_duration)} dk"

    return patterns


def get_routine_context() -> str:
    """Prompt'a eklenecek rutin bağlamı."""
    patterns = get_patterns()

    if not patterns:
        return ""

    lines = ["[USER PATTERNS - learned from behavior]"]

    if "peak_hours" in patterns:
        hours_str = ", ".join(f"{h}:00" for h in patterns["peak_hours"])
        lines.append(f"  Most active hours: {hours_str}")

    if "avg_start" in patterns:
        lines.append(f"  Usually starts day at: {patterns['avg_start']}")

    if "avg_end" in patterns:
        lines.append(f"  Usually goes offline at: {patterns['avg_end']}")

    if "top_apps" in patterns:
        apps = ", ".join(f"{name}({count})" for name, count in patterns["top_apps"][:3])
        lines.append(f"  Favorite apps: {apps}")

    if "avg_work_session" in patterns:
        lines.append(f"  Average work session: {patterns['avg_work_session']}")

    return "\n".join(lines)
