"""
Health Guardian — Kullanıcının fiziksel ve mental sağlığını koruyan sistem.
Göz sağlığı, uyku düzeni, su içme, duruş ve mental sağlık takibi yapar.
"""
import json
from datetime import datetime
from pathlib import Path
from threading import Lock

HEALTH_FILE = Path.home() / ".jarvis" / "memory" / "health.json"
_lock = Lock()


def _empty_health() -> dict:
    return {
        "water_log": [],              # Su içme kayıtları
        "screen_sessions": [],        # Ekran süresi kayıtları
        "sleep_log": [],              # Uyku kayıtları (first_seen/last_seen'den)
        "posture_reminders": 0,       # Bugünkü duruş hatırlatmaları
        "eye_rest_count": 0,          # Bugünkü göz dinlendirme
        "daily_steps_target": 8000,
        "water_target_ml": 2000,
        "weekly_mood_summary": {},    # Haftalık mood özeti
        "last_water_reminder": None,
        "last_eye_reminder": None,
        "last_posture_reminder": None,
        "today_date": None,
    }


class HealthGuardian:
    """Kullanıcının sağlık koruyucusu."""

    def __init__(self):
        self.data = self._load()
        self._check_day_reset()

    def _load(self) -> dict:
        try:
            if HEALTH_FILE.exists():
                d = json.loads(HEALTH_FILE.read_text(encoding="utf-8"))
                base = _empty_health()
                for k in base:
                    if k not in d:
                        d[k] = base[k]
                return d
        except Exception:
            pass
        return _empty_health()

    def _save(self):
        try:
            HEALTH_FILE.parent.mkdir(parents=True, exist_ok=True)
            self.data["water_log"] = self.data["water_log"][-100:]
            self.data["screen_sessions"] = self.data["screen_sessions"][-50:]
            self.data["sleep_log"] = self.data["sleep_log"][-30:]
            with _lock:
                HEALTH_FILE.write_text(
                    json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8"
                )
        except Exception:
            pass

    def _check_day_reset(self):
        """Gün değiştiğinde günlük sayaçları sıfırla."""
        today = datetime.now().strftime("%Y-%m-%d")
        if self.data.get("today_date") != today:
            self.data["today_date"] = today
            self.data["posture_reminders"] = 0
            self.data["eye_rest_count"] = 0
            self.data["last_water_reminder"] = None
            self.data["last_eye_reminder"] = None
            self.data["last_posture_reminder"] = None
            self._save()

    # ═══════════════════════════════════════════
    #  WATER TRACKING
    # ═══════════════════════════════════════════

    def log_water(self, ml: int = 250) -> str:
        """Su içme kaydı."""
        self.data["water_log"].append({
            "date": datetime.now().strftime("%Y-%m-%d"),
            "time": datetime.now().strftime("%H:%M"),
            "ml": ml,
        })
        self._save()
        today_total = self.get_today_water()
        target = self.data["water_target_ml"]
        pct = int(today_total / target * 100)
        return f"💧 {ml}ml kaydedildi! Bugün toplam: {today_total}ml ({pct}%)"

    def get_today_water(self) -> int:
        today = datetime.now().strftime("%Y-%m-%d")
        return sum(w["ml"] for w in self.data["water_log"] if w.get("date") == today)

    def should_remind_water(self) -> bool:
        """Su hatırlatması gerekli mi?"""
        last = self.data.get("last_water_reminder")
        if last:
            try:
                last_dt = datetime.fromisoformat(last)
                if (datetime.now() - last_dt).total_seconds() < 5400:  # 90 dk
                    return False
            except Exception:
                pass
        return True

    def mark_water_reminded(self):
        self.data["last_water_reminder"] = datetime.now().isoformat()
        self._save()

    # ═══════════════════════════════════════════
    #  EYE HEALTH
    # ═══════════════════════════════════════════

    def should_remind_eyes(self) -> bool:
        """20-20-20 kuralı hatırlatması gerekli mi?"""
        last = self.data.get("last_eye_reminder")
        if last:
            try:
                last_dt = datetime.fromisoformat(last)
                if (datetime.now() - last_dt).total_seconds() < 1200:  # 20 dk
                    return False
            except Exception:
                pass
        return True

    def mark_eye_reminded(self):
        self.data["last_eye_reminder"] = datetime.now().isoformat()
        self.data["eye_rest_count"] += 1
        self._save()

    # ═══════════════════════════════════════════
    #  SLEEP ANALYSIS
    # ═══════════════════════════════════════════

    def analyze_sleep(self, routines_data: dict) -> dict:
        """Uyku düzeni analizi (routines verisinden)."""
        first_seen = routines_data.get("daily_first_seen", {})
        last_seen = routines_data.get("daily_last_seen", {})

        if not first_seen or not last_seen:
            return {"status": "no_data"}

        sleep_hours = []
        dates = sorted(first_seen.keys())[-7:]

        for i in range(1, len(dates)):
            try:
                sleep_time = last_seen.get(dates[i - 1], "23:00")
                wake_time = first_seen.get(dates[i], "08:00")

                sh, sm = map(int, sleep_time.split(":"))
                wh, wm = map(int, wake_time.split(":"))

                sleep_minutes = sh * 60 + sm
                wake_minutes = wh * 60 + wm

                if sleep_minutes > wake_minutes:
                    duration = (1440 - sleep_minutes) + wake_minutes
                else:
                    duration = wake_minutes - sleep_minutes

                sleep_hours.append(duration / 60.0)
            except Exception:
                pass

        if not sleep_hours:
            return {"status": "insufficient_data"}

        avg_sleep = sum(sleep_hours) / len(sleep_hours)
        min_sleep = min(sleep_hours)
        max_sleep = max(sleep_hours)

        result = {
            "status": "ok",
            "avg_hours": round(avg_sleep, 1),
            "min_hours": round(min_sleep, 1),
            "max_hours": round(max_sleep, 1),
            "quality": "good" if avg_sleep >= 7 else "fair" if avg_sleep >= 6 else "poor",
            "days_analyzed": len(sleep_hours),
        }

        # Uyku kaydını güncelle
        self.data["sleep_log"].append({
            "date": datetime.now().strftime("%Y-%m-%d"),
            "avg_hours": result["avg_hours"],
            "quality": result["quality"],
        })
        self._save()

        return result

    # ═══════════════════════════════════════════
    #  MOOD TRACKING (haftalık)
    # ═══════════════════════════════════════════

    def record_mood(self, mood: str):
        """Günlük mood kaydı (haftalık özet için)."""
        today = datetime.now().strftime("%Y-%m-%d")
        self.data["weekly_mood_summary"][today] = mood
        # Son 14 gün tut
        keys = sorted(self.data["weekly_mood_summary"].keys())
        if len(keys) > 14:
            for k in keys[:-14]:
                del self.data["weekly_mood_summary"][k]
        self._save()

    def get_mood_trend(self) -> str:
        """Haftalık mood trendi."""
        moods = self.data.get("weekly_mood_summary", {})
        if len(moods) < 3:
            return "Yeterli mood verisi yok."

        recent = list(moods.values())[-7:]
        negative = sum(1 for m in recent if m in ("stressed", "sad", "tired"))
        positive = sum(1 for m in recent if m in ("happy", "excited"))

        if negative > len(recent) // 2:
            return f"⚠️ Son {len(recent)} günde çoğunlukla negatif mood ({negative}/{len(recent)}). Kendine zaman ayır."
        elif positive > len(recent) // 2:
            return f"😊 Son {len(recent)} günde çoğunlukla pozitif mood ({positive}/{len(recent)}). Harika gidiyorsun!"
        else:
            return f"📊 Son {len(recent)} günde dengeli mood. Pozitif: {positive}, Negatif: {negative}."

    # ═══════════════════════════════════════════
    #  OUTPUTS
    # ═══════════════════════════════════════════

    def get_health_report(self) -> str:
        """Genel sağlık raporu."""
        lines = ["🏥 Sağlık Raporu:"]

        # Su
        water = self.get_today_water()
        target = self.data["water_target_ml"]
        lines.append(f"  💧 Su: {water}/{target}ml (%{int(water / target * 100)})")

        # Göz dinlendirme
        lines.append(f"  👁️ Göz dinlendirme: {self.data['eye_rest_count']} kez bugün")

        # Mood trend
        lines.append(f"  🧠 {self.get_mood_trend()}")

        return "\n".join(lines)

    def get_prompt_context(self) -> str:
        """System prompt'a eklenecek sağlık bağlamı."""
        water = self.get_today_water()
        target = self.data["water_target_ml"]

        lines = ["[HEALTH AWARENESS]"]

        if water < target * 0.3:
            lines.append("  The user hasn't drunk enough water today. Casually remind them.")
        elif water >= target:
            lines.append("  Water intake is good today. ✓")

        # Mood trend kısa
        moods = self.data.get("weekly_mood_summary", {})
        if len(moods) >= 3:
            recent = list(moods.values())[-5:]
            negative = sum(1 for m in recent if m in ("stressed", "sad", "tired"))
            if negative >= 3:
                lines.append("  User has been feeling down recently. Be extra supportive.")

        return "\n".join(lines) if len(lines) > 1 else ""


def health_guardian_action(parameters: dict = None, player=None) -> str:
    """Tool olarak çağrılabilir sağlık action'ı."""
    guardian = HealthGuardian()
    params = parameters or {}
    action = params.get("action", "report")

    if action == "report":
        return guardian.get_health_report()
    elif action == "water":
        ml = int(params.get("ml", 250))
        return guardian.log_water(ml)
    elif action == "mood_trend":
        return guardian.get_mood_trend()
    else:
        return "Kullanılabilir: report, water, mood_trend"
