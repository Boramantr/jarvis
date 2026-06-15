"""
Daily Briefing Action — Sabah brifing: hava, takvim, motivasyon, haberler.
Kullanım: "Günaydın", "Bugünkü brifingimi ver", "Günün özeti"
"""
import json
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

try:
    import psutil
    _PSUTIL = True
except ImportError:
    _PSUTIL = False


def _get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


def _get_api_key() -> str:
    config_path = _get_base_dir() / "config" / "api_keys.json"
    with open(config_path, encoding="utf-8") as f:
        return json.load(f)["gemini_api_key"]


def _get_weather(city: str = "Lefke") -> str:
    """wttr.in API ile hava durumu al."""
    try:
        url = f"https://wttr.in/{city}?format=%C+%t+%h+%w&lang=tr"
        req = urllib.request.Request(url, headers={"User-Agent": "JARVIS/1.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            return resp.read().decode("utf-8").strip()
    except Exception:
        return "Hava durumu alınamadı"


def _get_weather_detailed(city: str = "Lefke") -> dict:
    """Detaylı hava durumu verisi."""
    try:
        url = f"https://wttr.in/{city}?format=j1"
        req = urllib.request.Request(url, headers={"User-Agent": "JARVIS/1.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            current = data.get("current_condition", [{}])[0]
            return {
                "temp": current.get("temp_C", "?"),
                "feels_like": current.get("FeelsLikeC", "?"),
                "humidity": current.get("humidity", "?"),
                "description": current.get("lang_tr", [{}])[0].get("value", current.get("weatherDesc", [{}])[0].get("value", "?")),
                "wind": current.get("windspeedKmph", "?"),
                "uv": current.get("uvIndex", "?"),
            }
    except Exception:
        return {}


def _get_system_status() -> str:
    """Sistem durumu özeti."""
    if not _PSUTIL:
        return ""

    try:
        cpu = psutil.cpu_percent(interval=0.5)
        ram = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        battery = psutil.sensors_battery()

        lines = []
        lines.append(f"CPU: %{cpu:.0f}")
        lines.append(f"RAM: %{ram.percent:.0f} ({ram.used // (1024**3)}/{ram.total // (1024**3)} GB)")
        lines.append(f"Disk: %{disk.percent:.0f} ({disk.free // (1024**3)} GB boş)")

        if battery:
            plug = "🔌 Şarjda" if battery.power_plugged else "🔋 Pilde"
            lines.append(f"Batarya: %{battery.percent:.0f} {plug}")

        return " | ".join(lines)
    except Exception:
        return ""


def _get_calendar_events() -> str:
    """Bugünkü takvim etkinlikleri."""
    try:
        calendar_file = Path.home() / ".jarvis" / "calendar" / "events.json"
        if calendar_file.exists():
            events = json.loads(calendar_file.read_text(encoding="utf-8"))
            today = datetime.now().strftime("%Y-%m-%d")
            today_events = [e for e in events if e.get("date") == today]
            if today_events:
                lines = []
                for e in sorted(today_events, key=lambda x: x.get("time", "00:00")):
                    time_info = f" ⏰ {e['time']}" if e.get("time") and e["time"] != "00:00" else ""
                    lines.append(f"  • {e['title']}{time_info}")
                return "\n".join(lines)
        return "Bugün takvimde etkinlik yok."
    except Exception:
        return "Takvime erişilemedi."


def _get_greeting() -> str:
    """Saate göre selamlama."""
    hour = datetime.now().hour
    if hour < 6:
        return "İyi geceler efendim, hâlâ ayaktasınız 🌙"
    elif hour < 12:
        return "Günaydın efendim ☀️"
    elif hour < 17:
        return "İyi öğleden sonralar efendim 🌤️"
    elif hour < 21:
        return "İyi akşamlar efendim 🌆"
    else:
        return "İyi geceler efendim 🌙"


def _get_motivational_quote() -> str:
    """Günün motivasyon sözü."""
    try:
        import google.generativeai as genai
        genai.configure(api_key=_get_api_key())
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(
            "Give me ONE short motivational quote (max 20 words) in Turkish. "
            "Return ONLY the quote, no attribution, no quotation marks."
        )
        return response.text.strip()
    except Exception:
        quotes = [
            "Bugün dünden daha iyi ol.",
            "Hayal et, planla, başar.",
            "Her yeni gün yeni bir fırsat.",
            "Kendine inan, gerisi gelir.",
            "Küçük adımlar büyük yolculuklar başlatır.",
        ]
        from random import choice
        return choice(quotes)


def _load_memory_city() -> str:
    """Hafızadan kullanıcının şehrini al."""
    try:
        memory_file = _get_base_dir() / "memory" / "long_term.json"
        if memory_file.exists():
            data = json.loads(memory_file.read_text(encoding="utf-8"))
            city_entry = data.get("identity", {}).get("city", {})
            city = city_entry.get("value", "") if isinstance(city_entry, dict) else str(city_entry)
            if city:
                return city.split(",")[0].strip()
    except Exception:
        pass
    return "Lefke"


def daily_briefing_action(parameters: dict = None, player=None) -> str:
    params = parameters or {}
    action = params.get("action", "full")

    if player:
        player.write_log("[Briefing] Günlük brifing hazırlanıyor...")

    city = _load_memory_city()
    now = datetime.now()

    if action == "weather":
        weather = _get_weather_detailed(city)
        if weather:
            return (
                f"🌤️ {city} Hava Durumu:\n"
                f"  🌡️ Sıcaklık: {weather['temp']}°C (Hissedilen: {weather['feels_like']}°C)\n"
                f"  💧 Nem: %{weather['humidity']}\n"
                f"  💨 Rüzgar: {weather['wind']} km/s\n"
                f"  ☀️ UV: {weather['uv']}\n"
                f"  📋 {weather['description']}"
            )
        return f"Hava durumu alınamadı ({city})."

    elif action == "motivation":
        return f"💪 {_get_motivational_quote()}"

    elif action == "system":
        status = _get_system_status()
        return f"💻 Sistem Durumu: {status}" if status else "Sistem durumu alınamadı."

    elif action == "calendar":
        return f"📅 Bugünkü Etkinlikler:\n{_get_calendar_events()}"

    # Full briefing
    greeting = _get_greeting()
    date_str = now.strftime("%d %B %Y, %A")
    time_str = now.strftime("%H:%M")

    weather = _get_weather_detailed(city)
    weather_text = ""
    if weather:
        weather_text = f"  🌡️ {weather['temp']}°C ({weather['description']}), Nem: %{weather['humidity']}"
    else:
        weather_text = f"  {_get_weather(city)}"

    calendar = _get_calendar_events()
    system = _get_system_status()
    quote = _get_motivational_quote()

    briefing = f"""{greeting}

📅 {date_str} — {time_str}

🌤️ Hava ({city}):
{weather_text}

📋 Takvim:
{calendar}

💻 Sistem: {system}

💬 "{quote}"
"""
    return briefing.strip()
