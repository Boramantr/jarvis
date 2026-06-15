"""
Creative Companion — JARVIS'in yaratıcı yönü.
Fikir jeneratörü, günlük tutma (journaling) ve öğrenme koçluğu sağlar.
"""
import json
import random
from datetime import datetime
from pathlib import Path
from threading import Lock

JOURNAL_FILE = Path.home() / ".jarvis" / "memory" / "journal.json"
_lock = Lock()


def _empty_journal() -> dict:
    return {"entries": []}


class CreativeCompanion:
    """JARVIS'in beraber düşünme ve yaratıcı fikir motoru."""

    def __init__(self):
        self.journal_data = self._load_journal()

    def _load_journal(self) -> dict:
        try:
            if JOURNAL_FILE.exists():
                d = json.loads(JOURNAL_FILE.read_text(encoding="utf-8"))
                if isinstance(d, dict) and "entries" in d:
                    return d
        except Exception:
            pass
        return _empty_journal()

    def _save_journal(self):
        try:
            JOURNAL_FILE.parent.mkdir(parents=True, exist_ok=True)
            with _lock:
                JOURNAL_FILE.write_text(
                    json.dumps(self.journal_data, ensure_ascii=False, indent=2), encoding="utf-8"
                )
        except Exception:
            pass

    # ═══════════════════════════════════════════
    #  JOURNALING
    # ═══════════════════════════════════════════

    def add_journal_entry(self, text: str, mood: str = "neutral") -> str:
        """Günlük girdisi ekle."""
        entry = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "text": text,
            "mood": mood
        }
        self.journal_data["entries"].append(entry)
        self._save_journal()
        return "📝 Günlüğüne kaydedildi."

    def read_journal(self, count: int = 3) -> str:
        """Son günlük girdilerini oku."""
        if not self.journal_data["entries"]:
            return "Günlüğün şu an boş."

        entries = self.journal_data["entries"][-count:]
        lines = ["📖 Son Günlük Girdileri:"]
        for e in reversed(entries):
            mood_icon = {"happy": "😊", "sad": "😔", "stressed": "😰", "excited": "🤩", "neutral": "😐", "tired": "😴"}.get(e.get("mood", "neutral"), "•")
            lines.append(f"[{e['date']}] {mood_icon} : {e['text']}")

        return "\n".join(lines)

    # ═══════════════════════════════════════════
    #  IDEA & BRAINSTORMING
    # ═══════════════════════════════════════════

    def generate_project_idea(self, domain: str = "software") -> str:
        """Rastgele proje fikirleri."""
        ideas = {
            "software": [
                "Ekrana bakma süreni ölçüp sana su içmeyi hatırlatan minik bir menü çubuğu uygulaması.",
                "Discord mesajlarındaki linkleri toplayıp özetleyen bir bot.",
                "Siber güvenlik açıklarını takip eden kişisel bir RSS terminal paneli.",
                "Kendi kişisel harcamalarını kategorize eden ve grafiğe döken bir Python CLI aracı.",
                "Mark-XXXIX benzeri ufak bir otonom drone simülasyonu."
            ],
            "cyber": [
                "Ev ağındaki cihazları periyodik tarayıp yeni bir cihaz gelince sana Telegram'dan yazan script.",
                "Popüler routerların default şifrelerini deneyen eğitim amaçlı bir audit scripti.",
                "Kendi basit keylogger'ını yazıp (kendi sistemin için) nasıl çalıştığını analiz etme."
            ],
            "general": [
                "30 günlük bir odaklanma challenge'ı planla.",
                "Odanın aydınlatmasını baştan aşağı yenilemek için bir kroki çıkar.",
                "Günde 15 dakika yeni bir dil (örn. İspanyolca veya Rust) çalış."
            ]
        }
        pool = ideas.get(domain, ideas["software"])
        return random.choice(pool)

    def rubber_duck(self) -> str:
        """Rubber duck debugging modu için başlangıç cümlesi."""
        prompts = [
            "Anlat bakalım, sorun ne? Kodun hangi satırında patlıyor?",
            "Şu anki hatayı bana bir ilkokul öğrencisine anlatır gibi anlatır mısın?",
            "Acaba değişkenin değeri beklediğin gibi değil mi? Print atıp baktın mı?",
            "Ben buradayım dostum. Akış diyagramını zihninde bir daha kur, nerede kopuyor?"
        ]
        return random.choice(prompts)


def creative_action(parameters: dict = None, player=None) -> str:
    """Tool olarak çağrılabilir yaratıcı yol arkadaşı action'ı."""
    engine = CreativeCompanion()
    params = parameters or {}
    action = params.get("action", "idea")

    if action == "idea":
        domain = params.get("domain", "software")
        return engine.generate_project_idea(domain)
    elif action == "journal_add":
        text = params.get("text", "")
        mood = params.get("mood", "neutral")
        if not text: return "Günlüğe yazacak bir şey söylemedin."
        return engine.add_journal_entry(text, mood)
    elif action == "journal_read":
        try:
            count = int(params.get("count", 3))
        except ValueError:
            count = 3
        return engine.read_journal(count)
    elif action == "rubber_duck":
        return engine.rubber_duck()
    else:
        return "Kullanılabilir: idea, journal_add, journal_read, rubber_duck"
