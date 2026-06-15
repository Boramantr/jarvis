"""
Calendar Manager Action — Kişisel takvim yönetimi (yerel JSON tabanlı).
Kullanım: "Yarın 14:00 toplantım var", "Bu haftaki etkinlikleri göster", "Etkinliği sil"
"""
import json
from datetime import datetime, timedelta
from pathlib import Path
from threading import Lock

CALENDAR_DIR = Path.home() / ".jarvis" / "calendar"
CALENDAR_FILE = CALENDAR_DIR / "events.json"
_lock = Lock()


def _load_events() -> list[dict]:
    try:
        if CALENDAR_FILE.exists():
            data = json.loads(CALENDAR_FILE.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return data
    except Exception:
        pass
    return []


def _save_events(events: list[dict]):
    CALENDAR_DIR.mkdir(parents=True, exist_ok=True)
    with _lock:
        CALENDAR_FILE.write_text(
            json.dumps(events, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )


def _parse_date(date_str: str) -> str:
    """Tarih string'ini YYYY-MM-DD formatına çevir."""
    today = datetime.now()
    date_lower = date_str.lower().strip()

    if date_lower in ("today", "bugün"):
        return today.strftime("%Y-%m-%d")
    elif date_lower in ("tomorrow", "yarın"):
        return (today + timedelta(days=1)).strftime("%Y-%m-%d")
    elif date_lower in ("yesterday", "dün"):
        return (today - timedelta(days=1)).strftime("%Y-%m-%d")

    day_map = {
        "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
        "friday": 4, "saturday": 5, "sunday": 6,
        "pazartesi": 0, "salı": 1, "çarşamba": 2, "perşembe": 3,
        "cuma": 4, "cumartesi": 5, "pazar": 6,
    }
    if date_lower in day_map:
        target_day = day_map[date_lower]
        current_day = today.weekday()
        days_ahead = target_day - current_day
        if days_ahead <= 0:
            days_ahead += 7
        target_date = today + timedelta(days=days_ahead)
        return target_date.strftime("%Y-%m-%d")

    try:
        parsed = datetime.strptime(date_str.strip(), "%Y-%m-%d")
        return parsed.strftime("%Y-%m-%d")
    except ValueError:
        pass

    try:
        parsed = datetime.strptime(date_str.strip(), "%d/%m/%Y")
        return parsed.strftime("%Y-%m-%d")
    except ValueError:
        pass

    return date_str.strip()


def calendar_manager_action(parameters: dict = None, player=None) -> str:
    params = parameters or {}
    action = params.get("action", "list")

    if player:
        player.write_log(f"[Calendar] Komut: {action}")

    events = _load_events()

    if action == "add":
        title = params.get("title", "").strip()
        date = params.get("date", "").strip()
        time_str = params.get("time", "").strip()
        description = params.get("description", "").strip()
        recurring = params.get("recurring", "").strip()  # daily, weekly, monthly

        if not title:
            return "Etkinlik adı belirtilmedi efendim."
        if not date:
            return "Etkinlik tarihi belirtilmedi."

        parsed_date = _parse_date(date)

        event = {
            "id": len(events) + 1,
            "title": title,
            "date": parsed_date,
            "time": time_str or "00:00",
            "description": description,
            "recurring": recurring,
            "created": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
        events.append(event)
        _save_events(events)

        time_info = f" saat {time_str}" if time_str else ""
        return f"Etkinlik kaydedildi: '{title}' — {parsed_date}{time_info}"

    elif action in ("list", "today", "week"):
        today = datetime.now().strftime("%Y-%m-%d")

        if action == "today":
            filtered = [e for e in events if e["date"] == today]
            label = "Bugünkü"
        elif action == "week":
            week_end = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
            filtered = [e for e in events if today <= e["date"] <= week_end]
            label = "Bu haftaki"
        else:
            filtered = sorted(events, key=lambda x: x["date"])[-15:]
            label = "Tüm"

        if not filtered:
            return f"{label} etkinlik bulunamadı efendim."

        filtered.sort(key=lambda x: (x["date"], x.get("time", "00:00")))
        lines = [f"📅 {label} Etkinlikler ({len(filtered)}):"]
        for e in filtered:
            time_info = f" ⏰ {e['time']}" if e.get("time") and e["time"] != "00:00" else ""
            lines.append(f"  #{e['id']} [{e['date']}]{time_info} — {e['title']}")
            if e.get("description"):
                lines.append(f"     📝 {e['description'][:60]}")
        return "\n".join(lines)

    elif action == "delete":
        event_id = params.get("id", "")
        title = params.get("title", "").lower()

        if event_id:
            try:
                eid = int(event_id)
                events = [e for e in events if e["id"] != eid]
                _save_events(events)
                return f"Etkinlik #{eid} silindi efendim."
            except ValueError:
                return "Geçersiz etkinlik ID'si."

        if title:
            before_count = len(events)
            events = [e for e in events if title not in e["title"].lower()]
            _save_events(events)
            deleted = before_count - len(events)
            return f"{deleted} etkinlik silindi efendim." if deleted else f"'{title}' ile eşleşen etkinlik bulunamadı."

        return "Silmek için etkinlik ID'si veya adı belirtin."

    elif action == "upcoming":
        now = datetime.now()
        today = now.strftime("%Y-%m-%d")
        current_time = now.strftime("%H:%M")
        upcoming = [
            e for e in events
            if e["date"] > today or (e["date"] == today and e.get("time", "23:59") >= current_time)
        ]
        upcoming.sort(key=lambda x: (x["date"], x.get("time", "00:00")))

        if not upcoming:
            return "Yaklaşan etkinlik yok efendim."

        lines = ["⏳ Yaklaşan Etkinlikler:"]
        for e in upcoming[:5]:
            time_info = f" ⏰ {e['time']}" if e.get("time") and e["time"] != "00:00" else ""
            lines.append(f"  [{e['date']}]{time_info} — {e['title']}")
        return "\n".join(lines)

    elif action == "clear_past":
        today = datetime.now().strftime("%Y-%m-%d")
        before = len(events)
        events = [e for e in events if e["date"] >= today or e.get("recurring")]
        _save_events(events)
        cleared = before - len(events)
        return f"{cleared} geçmiş etkinlik temizlendi efendim."

    return "Geçersiz takvim komutu. Kullanılabilir: add, list, today, week, delete, upcoming, clear_past"
