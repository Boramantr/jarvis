"""
Usage Tracker — Arka planda kullanım verilerini toplar.
JARVIS komut istatistikleri, uygulama süreleri, verimlilik metrikleri.
"""
import json
from datetime import datetime, timedelta
from pathlib import Path
from threading import Lock

TRACKER_DIR = Path.home() / ".jarvis" / "analytics"
_lock = Lock()


def _ensure_dir():
    TRACKER_DIR.mkdir(parents=True, exist_ok=True)


def _today_file() -> Path:
    return TRACKER_DIR / f"{datetime.now().strftime('%Y-%m-%d')}.json"


def _load_today() -> dict:
    try:
        f = _today_file()
        if f.exists():
            data = json.loads(f.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else _empty_day()
    except Exception:
        pass
    return _empty_day()


def _empty_day() -> dict:
    return {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "commands": {},           # {command_name: count}
        "total_commands": 0,
        "first_active": "",
        "last_active": "",
        "sessions": [],           # [{start, end, duration_min}]
        "apps_used": {},          # {app_name: seconds}
        "errors": 0,
    }


def _save_today(data: dict):
    _ensure_dir()
    with _lock:
        _today_file().write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )


def track_command(command_name: str):
    """Komut kullanımını kaydet."""
    data = _load_today()
    data["commands"][command_name] = data["commands"].get(command_name, 0) + 1
    data["total_commands"] = data.get("total_commands", 0) + 1

    now = datetime.now().strftime("%H:%M:%S")
    if not data["first_active"]:
        data["first_active"] = now
    data["last_active"] = now

    _save_today(data)


def track_error():
    """Hata sayısını artır."""
    data = _load_today()
    data["errors"] = data.get("errors", 0) + 1
    _save_today(data)


def track_app_time(app_name: str, seconds: float):
    """Uygulama kullanım süresini kaydet."""
    data = _load_today()
    data["apps_used"][app_name] = data["apps_used"].get(app_name, 0) + seconds
    _save_today(data)


def get_daily_stats(date_str: str = None) -> dict:
    """Günlük istatistikleri hesapla."""
    if date_str:
        f = TRACKER_DIR / f"{date_str}.json"
        try:
            if f.exists():
                return json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            pass
        return _empty_day()
    return _load_today()


def get_weekly_stats() -> dict:
    """Haftalık toplam istatistikler."""
    total_commands = 0
    total_errors = 0
    command_breakdown = {}
    app_total = {}
    days_active = 0

    for i in range(7):
        date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        day_data = get_daily_stats(date)

        if day_data.get("total_commands", 0) > 0:
            days_active += 1

        total_commands += day_data.get("total_commands", 0)
        total_errors += day_data.get("errors", 0)

        for cmd, count in day_data.get("commands", {}).items():
            command_breakdown[cmd] = command_breakdown.get(cmd, 0) + count

        for app, secs in day_data.get("apps_used", {}).items():
            app_total[app] = app_total.get(app, 0) + secs

    return {
        "days_active": days_active,
        "total_commands": total_commands,
        "total_errors": total_errors,
        "avg_commands_per_day": total_commands / max(days_active, 1),
        "top_commands": sorted(command_breakdown.items(), key=lambda x: x[1], reverse=True)[:10],
        "top_apps": sorted(app_total.items(), key=lambda x: x[1], reverse=True)[:10],
    }


def get_productivity_score() -> dict:
    """Basit verimlilik skoru hesapla."""
    data = _load_today()
    score = 0
    reasons = []

    total_cmds = data.get("total_commands", 0)

    # Komut miktarı
    if total_cmds >= 20:
        score += 25
        reasons.append("Yoğun komut kullanımı (+25)")
    elif total_cmds >= 10:
        score += 15
        reasons.append("İyi komut kullanımı (+15)")
    elif total_cmds >= 5:
        score += 10
        reasons.append("Orta komut kullanımı (+10)")

    # Çeşitlilik
    unique_commands = len(data.get("commands", {}))
    if unique_commands >= 5:
        score += 20
        reasons.append("Çeşitli komut kullanımı (+20)")
    elif unique_commands >= 3:
        score += 10
        reasons.append("Orta çeşitlilik (+10)")

    # Aktif süre
    if data.get("first_active") and data.get("last_active"):
        try:
            first = datetime.strptime(data["first_active"], "%H:%M:%S")
            last = datetime.strptime(data["last_active"], "%H:%M:%S")
            active_hours = (last - first).total_seconds() / 3600
            if active_hours >= 4:
                score += 25
                reasons.append(f"Uzun aktif süre: {active_hours:.1f}s (+25)")
            elif active_hours >= 2:
                score += 15
                reasons.append(f"İyi aktif süre: {active_hours:.1f}s (+15)")
        except Exception:
            pass

    # Hata oranı
    errors = data.get("errors", 0)
    if errors == 0:
        score += 15
        reasons.append("Hatasız çalışma (+15)")
    elif errors <= 2:
        score += 10
        reasons.append("Az hata (+10)")

    # Erken başlangıç bonusu
    if data.get("first_active"):
        try:
            hour = int(data["first_active"].split(":")[0])
            if hour < 9:
                score += 15
                reasons.append("Erken kuş bonusu (+15)")
        except Exception:
            pass

    return {
        "score": min(score, 100),
        "grade": "A+" if score >= 90 else "A" if score >= 80 else "B" if score >= 60 else "C" if score >= 40 else "D",
        "reasons": reasons,
    }
