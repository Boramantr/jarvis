"""
Emotion Engine — JARVIS'in duygusal zeka sistemi.
Kullanıcının duygusal durumunu analiz eder ve buna göre davranış önerir.
Ses tonu, kelime seçimi, zaman kalıpları ve aktivite bağlamından duygu çıkarımı yapar.
"""
import json
from collections import deque
from datetime import datetime
from pathlib import Path
from threading import Lock

EMOTION_FILE = Path.home() / ".jarvis" / "memory" / "emotional_state.json"
_lock = Lock()

# ─── Duygu Anahtar Kelimeleri (TR + EN) ───
MOOD_KEYWORDS = {
    "happy": [
        "mutlu", "harika", "süper", "mükemmel", "güzel", "muhteşem",
        "happy", "great", "awesome", "amazing", "love", "perfect",
        "seviyorum", "bayıldım", "efsane", "çok iyi", "tebrikler",
        "yey", "woohoo", "bravo", "helal",
    ],
    "stressed": [
        "stres", "sinir", "sinirli", "sıkıldım", "bıktım", "kızgın",
        "stressed", "angry", "annoyed", "frustrated", "ugh",
        "sınav", "deadline", "yetişmiyor", "çok iş", "kafayı yicem",
        "saçmalık", "rezalet", "berbat", "olmadı",
    ],
    "sad": [
        "üzgün", "kötü", "mutsuz", "moral", "yalnız", "karamsar",
        "sad", "depressed", "lonely", "down", "miss", "özledim",
        "ağla", "zor", "dayanamıyorum", "canım sıkkın",
    ],
    "excited": [
        "heyecanlı", "sabırsız", "oha", "vay", "inanamıyorum",
        "excited", "can't wait", "woah", "wow", "incredible",
        "acayip", "delircem", "çıldırıyorum",
    ],
    "tired": [
        "yorgun", "uykusuz", "bitkin", "tükenmiş", "uyku",
        "tired", "exhausted", "sleepy", "drained",
        "baş ağrısı", "gözlerim yanıyor", "bitiyorum",
    ],
    "focused": [
        "odaklan", "çalışıyorum", "kodluyorum", "meşgul",
        "focus", "working", "coding", "busy", "concentrate",
    ],
    "curious": [
        "merak", "nasıl yapılır", "neden", "araştır", "öğren",
        "curious", "how does", "why", "research", "interesting",
        "ilginç", "acaba",
    ],
}

# Mood → varsayılan enerji seviyeleri
MOOD_ENERGY = {
    "happy": 0.8, "excited": 0.9, "focused": 0.7, "curious": 0.65,
    "neutral": 0.5, "tired": 0.25, "stressed": 0.4, "sad": 0.3,
}

# Mood → UI renk/animasyon ipuçları
MOOD_UI_HINTS = {
    "happy":    {"hue": "warm_gold",    "intensity": 0.8, "pulse_speed": 1.2, "rgb": (255, 200, 60)},
    "excited":  {"hue": "bright_cyan",  "intensity": 0.9, "pulse_speed": 1.5, "rgb": (0, 230, 255)},
    "focused":  {"hue": "cool_blue",    "intensity": 0.6, "pulse_speed": 0.8, "rgb": (60, 140, 220)},
    "curious":  {"hue": "soft_purple",  "intensity": 0.7, "pulse_speed": 1.0, "rgb": (150, 120, 255)},
    "neutral":  {"hue": "sky_blue",     "intensity": 0.5, "pulse_speed": 1.0, "rgb": (0, 191, 255)},
    "tired":    {"hue": "dim_blue",     "intensity": 0.3, "pulse_speed": 0.5, "rgb": (60, 100, 160)},
    "stressed": {"hue": "amber",        "intensity": 0.7, "pulse_speed": 1.4, "rgb": (255, 160, 40)},
    "sad":      {"hue": "deep_purple",  "intensity": 0.4, "pulse_speed": 0.6, "rgb": (100, 80, 180)},
}

# Prompt'a eklenecek mood açıklamaları
MOOD_DESCRIPTIONS = {
    "happy":    "The user seems happy and positive. Match their energy, be warm and celebratory.",
    "excited":  "The user is excited! Share their enthusiasm, be energetic.",
    "focused":  "The user is deep in focus. Be ultra-concise, technical, don't distract.",
    "curious":  "The user is curious and exploring. Be informative and engaging.",
    "neutral":  "The user is in a neutral state. Be your normal self.",
    "tired":    "The user seems tired. Be gentle, brief, and suggest rest if appropriate.",
    "stressed": "The user seems stressed. Be calming, supportive, offer practical help.",
    "sad":      "The user seems down. Be empathetic and warm. Don't be fake-cheerful.",
}


class EmotionEngine:
    """JARVIS'in duygusal zeka motoru — kullanıcıyı 'hisseder'."""

    def __init__(self):
        self.current_mood = "neutral"
        self.energy_level = 0.5
        self.mood_confidence = 0.0
        self.mood_history: deque = deque(maxlen=100)
        self._interaction_count = 0
        self._load_state()

    # ═══════════════════════════════════════════
    #  PERSISTENCE
    # ═══════════════════════════════════════════

    def _load_state(self):
        try:
            if EMOTION_FILE.exists():
                data = json.loads(EMOTION_FILE.read_text(encoding="utf-8"))
                self.current_mood = data.get("current_mood", "neutral")
                self.energy_level = data.get("energy_level", 0.5)
                self._interaction_count = data.get("interaction_count", 0)
                for entry in data.get("mood_history", [])[-100:]:
                    self.mood_history.append(entry)
        except Exception:
            pass

    def _save_state(self):
        try:
            EMOTION_FILE.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "current_mood": self.current_mood,
                "energy_level": round(self.energy_level, 2),
                "mood_confidence": round(self.mood_confidence, 2),
                "interaction_count": self._interaction_count,
                "last_updated": datetime.now().isoformat(),
                "mood_history": list(self.mood_history)[-100:],
            }
            with _lock:
                EMOTION_FILE.write_text(
                    json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
                )
        except Exception:
            pass

    # ═══════════════════════════════════════════
    #  ANALYSIS
    # ═══════════════════════════════════════════

    def analyze_text(self, text: str) -> str:
        """Metin girdisinden duygu analizi yap."""
        if not text or len(text) < 2:
            return self.current_mood

        text_lower = text.lower()
        scores = {}

        for mood, keywords in MOOD_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > 0:
                scores[mood] = score

        if scores:
            best_mood = max(scores, key=scores.get)
            self.mood_confidence = min(scores[best_mood] / 3.0, 1.0)
            self._update_mood(best_mood)

        self._interaction_count += 1
        return self.current_mood

    def analyze_context(self, hour: int = None, work_minutes: int = 0,
                        app_category: str = "other") -> str:
        """Bağlamsal sinyallerden duygu analizi."""
        if hour is None:
            hour = datetime.now().hour

        # Zaman bazlı enerji haritası
        time_energy_map = [
            (0, 6, 0.2), (6, 9, 0.6), (9, 12, 0.8), (12, 14, 0.6),
            (14, 18, 0.7), (18, 22, 0.5), (22, 24, 0.3),
        ]
        time_energy = 0.5
        for start, end, energy in time_energy_map:
            if start <= hour < end:
                time_energy = energy
                break

        # Gece geç saatte çalışma → yorgun
        if 0 <= hour < 6 and work_minutes > 60:
            self._update_mood("tired")

        # Uzun çalışma → yorgunluk
        if work_minutes > 180:
            time_energy *= 0.6
            if self.current_mood not in ("excited", "happy"):
                self._update_mood("tired")
        elif work_minutes > 120:
            time_energy *= 0.8

        # Uygulama bağlamı
        if app_category == "gaming":
            if self.current_mood != "excited":
                self._update_mood("excited")
            time_energy = max(time_energy, 0.7)
        elif app_category == "coding":
            if self.current_mood == "neutral":
                self._update_mood("focused")

        # Yumuşak enerji geçişi
        self.energy_level += (time_energy - self.energy_level) * 0.2
        self.energy_level = max(0.1, min(1.0, self.energy_level))

        self._save_state()
        return self.current_mood

    def _update_mood(self, new_mood: str):
        """Mood'u güncelle ve geçmişe kaydet."""
        if new_mood == self.current_mood:
            return

        old_mood = self.current_mood
        self.current_mood = new_mood
        self.energy_level = MOOD_ENERGY.get(new_mood, 0.5)

        self.mood_history.append({
            "time": datetime.now().strftime("%H:%M"),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "from": old_mood,
            "to": new_mood,
            "confidence": round(self.mood_confidence, 2),
        })
        self._save_state()

    # ═══════════════════════════════════════════
    #  OUTPUTS
    # ═══════════════════════════════════════════

    def get_prompt_context(self) -> str:
        """System prompt'a eklenecek duygusal bağlam."""
        desc = MOOD_DESCRIPTIONS.get(self.current_mood, MOOD_DESCRIPTIONS["neutral"])
        energy_word = "low" if self.energy_level < 0.4 else "moderate" if self.energy_level < 0.7 else "high"

        return (
            f"[EMOTIONAL AWARENESS]\n"
            f"  User mood: {self.current_mood} (confidence: {self.mood_confidence:.0%})\n"
            f"  Energy level: {energy_word} ({self.energy_level:.0%})\n"
            f"  Guidance: {desc}\n"
            f"  Today's interactions: {self._interaction_count}"
        )

    def get_ui_hints(self) -> dict:
        """UI için mood renk/animasyon ipuçları döndür."""
        return MOOD_UI_HINTS.get(self.current_mood, MOOD_UI_HINTS["neutral"])

    def get_mood_summary(self) -> str:
        """Günlük mood özeti."""
        today = datetime.now().strftime("%Y-%m-%d")
        today_moods = [m for m in self.mood_history if m.get("date") == today]

        if not today_moods:
            return f"Ruh hali: {self.current_mood} | Enerji: %{int(self.energy_level * 100)}"

        mood_counts = {}
        for m in today_moods:
            mood_counts[m["to"]] = mood_counts.get(m["to"], 0) + 1
        dominant = max(mood_counts, key=mood_counts.get)

        return (
            f"Ruh hali: {self.current_mood} | Enerji: %{int(self.energy_level * 100)} | "
            f"Bugün baskın: {dominant} | Mood değişimi: {len(today_moods)}"
        )

    def should_comfort(self) -> bool:
        return self.current_mood in ("sad", "stressed") and self.mood_confidence > 0.4

    def should_celebrate(self) -> bool:
        return self.current_mood in ("happy", "excited") and self.mood_confidence > 0.4
