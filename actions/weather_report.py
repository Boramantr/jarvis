"""
Weather Report Action — Gerçek API verileri ile hava durumu.
Kullanım: "Hava nasıl?", "Yarın yağmur yağacak mı?", "Bu hafta hava nasıl?"
"""
import json
import urllib.request
from urllib.parse import quote_plus


def _fetch_weather(city: str, format_str: str = "j1") -> dict:
    """wttr.in API ile hava durumu verisi al."""
    try:
        url = f"https://wttr.in/{quote_plus(city)}?format={format_str}&lang=tr"
        req = urllib.request.Request(url, headers={"User-Agent": "JARVIS/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            if format_str == "j1":
                return json.loads(resp.read().decode("utf-8"))
            return {"text": resp.read().decode("utf-8").strip()}
    except Exception as e:
        return {"error": str(e)}


def _clothing_advice(temp: int, rain_chance: int) -> str:
    """Sıcaklığa göre giyim önerisi."""
    if temp <= 0:
        return "🧥 Çok kalın giyin, mont ve atkı şart!"
    elif temp <= 10:
        return "🧥 Kalın giyin, hava soğuk."
    elif temp <= 18:
        return "🧶 Hafif ceket veya hırka yeterli."
    elif temp <= 25:
        return "👕 Rahat giyin, hava güzel."
    elif temp <= 32:
        return "🩳 Hafif ve açık renkli giyin, sıcak."
    else:
        return "🥵 Çok sıcak! Güneş kremi ve bol su şart."

    if rain_chance > 50:
        return "☂️ Şemsiye almayı unutma!"


def _uv_advice(uv_index: int) -> str:
    """UV indeksine göre tavsiye."""
    if uv_index <= 2:
        return "Düşük UV"
    elif uv_index <= 5:
        return "Orta UV — Güneş gözlüğü önerilir"
    elif uv_index <= 7:
        return "Yüksek UV — Güneş kremi kullan"
    elif uv_index <= 10:
        return "Çok yüksek UV — Dışarıda dikkatli ol"
    else:
        return "Aşırı UV — Mümkünse dışarı çıkma"


def weather_report_action(parameters: dict = None, player=None, session_memory=None) -> str:
    params = parameters or {}
    city = params.get("city", "Lefke")
    when = params.get("time", "today").strip().lower()

    if not city or not isinstance(city, str) or not city.strip():
        return "Şehir adı belirtilmedi efendim."

    city = city.strip()

    if player:
        player.write_log(f"[Weather] {city} — {when}")

    data = _fetch_weather(city)

    if "error" in data:
        # Fallback: Browser ile aç
        import webbrowser
        url = f"https://www.google.com/search?q=weather+in+{quote_plus(city)}+{quote_plus(when)}"
        webbrowser.open(url)
        return f"API hatası, tarayıcıda açıldı: {data['error']}"

    try:
        current = data.get("current_condition", [{}])[0]
        temp = int(current.get("temp_C", 0))
        feels_like = current.get("FeelsLikeC", "?")
        humidity = current.get("humidity", "?")
        wind_speed = current.get("windspeedKmph", "?")
        wind_dir = current.get("winddir16Point", "")
        uv = int(current.get("uvIndex", 0))
        visibility = current.get("visibility", "?")

        # Türkçe açıklama
        desc_list = current.get("lang_tr", [])
        description = desc_list[0].get("value", "") if desc_list else ""
        if not description:
            desc_en = current.get("weatherDesc", [{}])
            description = desc_en[0].get("value", "?") if desc_en else "?"

        if when == "today" or when == "bugün":
            weather_data = data.get("weather", [{}])
            today_data = weather_data[0] if weather_data else {}
            max_temp = today_data.get("maxtempC", "?")
            min_temp = today_data.get("mintempC", "?")
            rain_chance = 0
            hourly = today_data.get("hourly", [])
            if hourly:
                rain_chances = [int(h.get("chanceofrain", 0)) for h in hourly]
                rain_chance = max(rain_chances) if rain_chances else 0

            clothing = _clothing_advice(temp, rain_chance)
            uv_text = _uv_advice(uv)

            return (
                f"🌤️ {city} — Şu An:\n"
                f"  🌡️ Sıcaklık: {temp}°C (Hissedilen: {feels_like}°C)\n"
                f"  📊 Min/Max: {min_temp}°C / {max_temp}°C\n"
                f"  💧 Nem: %{humidity}\n"
                f"  💨 Rüzgar: {wind_speed} km/s {wind_dir}\n"
                f"  ☀️ UV: {uv} ({uv_text})\n"
                f"  👁️ Görüş: {visibility} km\n"
                f"  🌧️ Yağmur: %{rain_chance}\n"
                f"  📋 {description}\n"
                f"  {clothing}"
            )

        elif when in ("tomorrow", "yarın"):
            weather_data = data.get("weather", [])
            if len(weather_data) >= 2:
                tomorrow = weather_data[1]
                max_t = tomorrow.get("maxtempC", "?")
                min_t = tomorrow.get("mintempC", "?")
                hourly = tomorrow.get("hourly", [])
                rain_chance = 0
                if hourly:
                    rain_chances = [int(h.get("chanceofrain", 0)) for h in hourly]
                    rain_chance = max(rain_chances) if rain_chances else 0
                    desc_list = hourly[4].get("lang_tr", []) if len(hourly) > 4 else []
                    desc = desc_list[0].get("value", "") if desc_list else "?"
                else:
                    desc = "?"

                clothing = _clothing_advice(int(max_t) if max_t != "?" else 20, rain_chance)
                return (
                    f"📅 {city} — Yarın:\n"
                    f"  🌡️ Min/Max: {min_t}°C / {max_t}°C\n"
                    f"  🌧️ Yağmur: %{rain_chance}\n"
                    f"  📋 {desc}\n"
                    f"  {clothing}"
                )
            return "Yarınki hava verisi alınamadı."

        elif when in ("week", "this week", "hafta", "bu hafta"):
            weather_data = data.get("weather", [])
            if not weather_data:
                return "Haftalık hava verisi alınamadı."

            lines = [f"📅 {city} — 3 Günlük Tahmin:"]
            for day in weather_data[:3]:
                date = day.get("date", "?")
                max_t = day.get("maxtempC", "?")
                min_t = day.get("mintempC", "?")
                hourly = day.get("hourly", [])
                rain = 0
                if hourly:
                    rain = max(int(h.get("chanceofrain", 0)) for h in hourly)
                rain_icon = "🌧️" if rain > 50 else "☁️" if rain > 20 else "☀️"
                lines.append(f"  {rain_icon} {date}: {min_t}°C - {max_t}°C (Yağmur: %{rain})")
            return "\n".join(lines)

        else:
            # Genel arama
            return (
                f"🌤️ {city}: {temp}°C, {description}\n"
                f"  Nem: %{humidity}, Rüzgar: {wind_speed} km/s"
            )

    except Exception as e:
        return f"Hava durumu işlenirken hata: {e}"
