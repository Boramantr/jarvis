"""
Circadian Engine — JARVIS'in biyolojik saati.
Kullanıcının gerçek rutinleriyle senkronize olur.
Sabit TIME_BASED_MODES yerine, öğrenilmiş ritim kullanır.
"""
import json
import math
from datetime import datetime
from pathlib import Path
from threading import Lock

CIRCADIAN_FILE = Path.home() / ".jarvis" / "memory" / "circadian.json"
_lock = Lock()


def _default_rhythm() -> dict:
    return {
        "learned_wake_hour": 8.0,
        "learned_sleep_hour": 0.0,
        "peak_hours": [10, 14, 21],
        "low_hours": [3, 4, 5, 13],
        "energy_curve": {},
        "last_updated": None,
        "data_points": 0,
    }


class CircadianEngine:
    """JARVIS'in biyolojik saati — kullanıcıyla senkronize."""

    def __init__(self):
        self.data = self._load()
        self._jarvis_energy = 0.5

    def _load(self) -> dict:
        try:
            if CIRCADIAN_FILE.exists():
                d = json.loads(CIRCADIAN_FILE.read_text(encoding="utf-8"))
                base = _default_rhythm()
                for k in base:
                    if k not in d:
                        d[k] = base[k]
                return d
        except Exception:
            pass
        return _default_rhythm()

    def _save(self):
        try:
            CIRCADIAN_FILE.parent.mkdir(parents=True, exist_ok=True)
            with _lock:
                CIRCADIAN_FILE.write_text(
                    json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8"
                )
        except Exception:
            pass

    # ═══════════════════════════════════════════
    #  LEARNING
    # ═══════════════════════════════════════════

    def learn_from_routines(self, routines_data: dict):
        """routines.py verisinden ritim öğren."""
        first_seen = routines_data.get("daily_first_seen", {})
        last_seen = routines_data.get("daily_last_seen", {})
        active_hours = routines_data.get("active_hours", [])

        if not first_seen:
            return

        # Ortalama uyanış saati
        wake_times = []
        for t in list(first_seen.values())[-14:]:
            try:
                h, m = t.split(":")
                wake_times.append(int(h) + int(m) / 60.0)
            except Exception:
                pass
        if wake_times:
            self.data["learned_wake_hour"] = round(sum(wake_times) / len(wake_times), 1)

        # Ortalama uyku saati
        sleep_times = []
        for t in list(last_seen.values())[-14:]:
            try:
                h, m = t.split(":")
                val = int(h) + int(m) / 60.0
                sleep_times.append(val)
            except Exception:
                pass
        if sleep_times:
            self.data["learned_sleep_hour"] = round(sum(sleep_times) / len(sleep_times), 1)

        # En aktif ve en düşük saatler
        if active_hours:
            from collections import Counter
            hour_counts = Counter(active_hours)
            if hour_counts:
                sorted_hours = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)
                self.data["peak_hours"] = [h for h, _ in sorted_hours[:4]]
                all_hours = set(range(24))
                active_set = set(hour_counts.keys())
                inactive = all_hours - active_set
                self.data["low_hours"] = sorted(inactive)[:6]

        # Saatlik enerji eğrisi oluştur
        curve = {}
        total = sum(hour_counts.values()) if active_hours else 1
        for h in range(24):
            count = hour_counts.get(h, 0) if active_hours else 0
            curve[str(h)] = round(count / max(total, 1) * 24, 2)
        self.data["energy_curve"] = curve

        self.data["data_points"] = len(first_seen)
        self.data["last_updated"] = datetime.now().strftime("%Y-%m-%d")
        self._save()

    def get_jarvis_energy(self) -> float:
        """JARVIS'in şu anki enerji seviyesi (0-1)."""
        hour = datetime.now().hour
        wake = self.data["learned_wake_hour"]
        sleep = self.data["learned_sleep_hour"]

        # Öğrenilmiş eğri varsa kullan
        curve = self.data.get("energy_curve", {})
        if curve and str(hour) in curve:
            raw = curve[str(hour)]
            self._jarvis_energy = max(0.1, min(1.0, raw))
            return self._jarvis_energy

        # Yoksa basit sinüs modeli
        if sleep > 12:
            awake_hours = sleep - wake
        else:
            awake_hours = (24 - wake) + sleep

        hours_since_wake = (hour - wake) % 24
        if awake_hours > 0:
            phase = hours_since_wake / awake_hours
        else:
            phase = 0.5

        # Sabah yükseliş, öğle dip, öğleden sonra tekrar yükseliş, gece düşüş
        energy = 0.5 + 0.4 * math.sin(phase * math.pi)
        # Gece saatlerinde düşür
        if 2 <= hour <= 6:
            energy *= 0.3
        elif 0 <= hour < 2 or 23 <= hour:
            energy *= 0.5

        self._jarvis_energy = max(0.1, min(1.0, energy))
        return self._jarvis_energy

    def get_time_personality(self) -> dict:
        """Saate göre kişilik modifikasyonları — öğrenilmiş ritme göre."""
        hour = datetime.now().hour
        energy = self.get_jarvis_energy()
        wake = self.data["learned_wake_hour"]

        hours_awake = (hour - wake) % 24

        if hours_awake < 1:
            return {
                "mode": "waking_up",
                "tone": "Yavaş yavaş uyanıyor. Sıcak ve nazik selamla.",
                "energy_word": "uyanıyor",
                "speech_speed": "slow",
            }
        elif energy > 0.7:
            return {
                "mode": "peak",
                "tone": "Enerjik ve verimli. Hızlı, net yanıtlar ver.",
                "energy_word": "enerjik",
                "speech_speed": "normal",
            }
        elif energy > 0.4:
            return {
                "mode": "normal",
                "tone": "Normal tempo. Dengeli ve doğal.",
                "energy_word": "normal",
                "speech_speed": "normal",
            }
        elif energy > 0.2:
            return {
                "mode": "winding_down",
                "tone": "Sakinleşme vakti. Rahat ve sessiz tonla.",
                "energy_word": "sakin",
                "speech_speed": "calm",
            }
        else:
            return {
                "mode": "sleep_mode",
                "tone": "Çok geç saat. Fısıltı modunda, kısa yanıtlar. Uyku öner.",
                "energy_word": "uyku",
                "speech_speed": "whisper",
            }

    def get_prompt_context(self) -> str:
        """System prompt'a eklenecek circadian bağlam."""
        tp = self.get_time_personality()
        energy = self.get_jarvis_energy()

        return (
            f"[CIRCADIAN RHYTHM]\n"
            f"  JARVIS energy: {energy:.0%} ({tp['energy_word']})\n"
            f"  Mode: {tp['mode']}\n"
            f"  Tone guidance: {tp['tone']}\n"
            f"  User usually wakes at: {self.data['learned_wake_hour']:.0f}:00\n"
            f"  User usually sleeps at: {self.data['learned_sleep_hour']:.0f}:00"
        )

    def is_unusual_hour(self) -> bool:
        """Kullanıcı normalde bu saatte aktif mi?"""
        hour = datetime.now().hour
        return hour in self.data.get("low_hours", [])
