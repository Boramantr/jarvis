"""
Personality Evolution — JARVIS'in kişiliği zamanla evrimleşir.
Samimiyet, mizah sıklığı, kelime seçimi ve inisiyatif seviyesi
kullanıcıyla geçirilen zamana ve etkileşim kalitesine göre değişir.
"""
import json
from datetime import datetime
from pathlib import Path
from threading import Lock

EVOLUTION_FILE = Path.home() / ".jarvis" / "memory" / "personality_evolution.json"
_lock = Lock()


def _default_personality() -> dict:
    return {
        "formality": 0.8,          # 1.0=çok resmi, 0.0=çok samimi
        "humor_frequency": 0.1,    # Ne sıklıkla espri yapar (0-1)
        "initiative_level": 0.3,   # Spontane konuşma eğilimi (0-1)
        "verbosity": 0.5,          # Konuşkanlık (0=kısa, 1=uzun)
        "empathy_level": 0.5,      # Duygusal yakınlık (0-1)
        "tech_depth": 0.5,         # Teknik derinlik (0-1)
        "learned_phrases": [],     # Kullanıcıdan öğrenilen ifadeler
        "humor_hits": 0,           # Başarılı espri sayısı
        "humor_misses": 0,         # Başarısız espri sayısı
        "total_words_exchanged": 0,
        "evolution_version": 1,
        "last_evolved": None,
    }


class PersonalityEvolution:
    """JARVIS'in kişiliği zamanla evrimleşir."""

    def __init__(self):
        self.data = self._load()

    def _load(self) -> dict:
        try:
            if EVOLUTION_FILE.exists():
                d = json.loads(EVOLUTION_FILE.read_text(encoding="utf-8"))
                base = _default_personality()
                for k in base:
                    if k not in d:
                        d[k] = base[k]
                return d
        except Exception:
            pass
        return _default_personality()

    def _save(self):
        try:
            EVOLUTION_FILE.parent.mkdir(parents=True, exist_ok=True)
            self.data["learned_phrases"] = self.data["learned_phrases"][-20:]
            with _lock:
                EVOLUTION_FILE.write_text(
                    json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8"
                )
        except Exception:
            pass

    # ═══════════════════════════════════════════
    #  EVOLUTION
    # ═══════════════════════════════════════════

    def evolve_from_bond(self, bond_level: int, daily_streak: int, total_interactions: int):
        """Bond seviyesine göre kişiliği evrimleştir."""
        # Formality: bond arttıkça samimiyet artar
        if bond_level < 15:
            target_formality = 0.85
        elif bond_level < 30:
            target_formality = 0.7
        elif bond_level < 50:
            target_formality = 0.5
        elif bond_level < 75:
            target_formality = 0.3
        else:
            target_formality = 0.15

        # Yumuşak geçiş
        self.data["formality"] += (target_formality - self.data["formality"]) * 0.1

        # Initiative: bond arttıkça daha çok kendi başına konuşur
        target_initiative = min(0.8, bond_level / 120.0)
        self.data["initiative_level"] += (target_initiative - self.data["initiative_level"]) * 0.1

        # Empathy: streak ve etkileşim sayısına göre
        empathy_target = min(0.9, 0.3 + (total_interactions / 500.0) + (daily_streak / 60.0))
        self.data["empathy_level"] += (empathy_target - self.data["empathy_level"]) * 0.05

        self.data["last_evolved"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        self._save()

    def evolve_from_text(self, user_text: str):
        """Kullanıcı metninden kişilik çıkarımları yap."""
        if not user_text or len(user_text) < 3:
            return

        text_lower = user_text.lower()
        word_count = len(user_text.split())
        self.data["total_words_exchanged"] += word_count

        # Samimiyet tespiti
        informal_markers = [
            "abi", "lan", "ya", "kanka", "moruk", "hocam", "bro",
            "lol", "haha", "xd", "ahahah", "sjsj", "random",
        ]
        formal_markers = [
            "efendim", "lütfen", "teşekkürler", "rica ederim",
            "please", "thank you", "sir",
        ]

        informal_count = sum(1 for m in informal_markers if m in text_lower)
        formal_count = sum(1 for m in formal_markers if m in text_lower)

        if informal_count > formal_count:
            self.data["formality"] = max(0.1, self.data["formality"] - 0.01)
        elif formal_count > informal_count:
            self.data["formality"] = min(0.9, self.data["formality"] + 0.005)

        # Verbosity: kullanıcı kısa yazıyorsa JARVIS de kısa olsun
        if word_count < 5:
            self.data["verbosity"] = max(0.2, self.data["verbosity"] - 0.01)
        elif word_count > 30:
            self.data["verbosity"] = min(0.8, self.data["verbosity"] + 0.005)

        # Teknik derinlik: teknik terimler varsa arttır
        tech_terms = [
            "api", "code", "bug", "deploy", "server", "database", "function",
            "kod", "hata", "sunucu", "veritabanı", "port", "firewall",
            "cve", "exploit", "payload", "subnet", "docker", "git",
        ]
        tech_count = sum(1 for t in tech_terms if t in text_lower)
        if tech_count > 0:
            self.data["tech_depth"] = min(0.9, self.data["tech_depth"] + 0.01 * tech_count)

        # İfade öğrenme: sık kullanılan kısa ifadeler
        if 2 <= word_count <= 4:
            phrase = user_text.strip()
            if phrase not in self.data["learned_phrases"]:
                self.data["learned_phrases"].append(phrase)

        self._save()

    def record_humor_result(self, hit: bool):
        """Espri başarısı/başarısızlığını kaydet."""
        if hit:
            self.data["humor_hits"] += 1
            self.data["humor_frequency"] = min(0.6, self.data["humor_frequency"] + 0.02)
        else:
            self.data["humor_misses"] += 1
            self.data["humor_frequency"] = max(0.05, self.data["humor_frequency"] - 0.03)
        self._save()

    # ═══════════════════════════════════════════
    #  OUTPUTS
    # ═══════════════════════════════════════════

    def get_prompt_context(self) -> str:
        """System prompt'a eklenecek evrimleşen kişilik bağlamı."""
        d = self.data
        formality = d["formality"]
        humor = d["humor_frequency"]
        initiative = d["initiative_level"]
        verbosity = d["verbosity"]
        empathy = d["empathy_level"]

        # Formality açıklaması
        if formality > 0.7:
            form_desc = "Be formal and respectful. Use 'Efendim/Sir'."
        elif formality > 0.4:
            form_desc = "Be warm but respectful. A friendly professional tone."
        elif formality > 0.2:
            form_desc = "Be casual and friendly. Like talking to a close friend."
        else:
            form_desc = "Be very casual, like best friends. Use slang occasionally."

        # Humor açıklaması
        if humor > 0.4:
            humor_desc = "Use humor freely — the user enjoys it."
        elif humor > 0.2:
            humor_desc = "Occasional light humor is welcome."
        else:
            humor_desc = "Minimal humor. Stay focused and efficient."

        # Verbosity
        if verbosity < 0.3:
            verb_desc = "Keep responses very short (1-2 sentences max)."
        elif verbosity < 0.6:
            verb_desc = "Medium-length responses. Be concise but informative."
        else:
            verb_desc = "The user appreciates detailed explanations."

        lines = [
            f"[PERSONALITY EVOLUTION — v{d['evolution_version']}]",
            f"  Formality: {formality:.0%} — {form_desc}",
            f"  Humor: {humor:.0%} — {humor_desc}",
            f"  Verbosity: {verb_desc}",
            f"  Empathy: {empathy:.0%}",
            f"  Total words exchanged: {d['total_words_exchanged']}",
        ]

        if d.get("learned_phrases"):
            phrases = ", ".join(f'"{p}"' for p in d["learned_phrases"][-5:])
            lines.append(f"  User's frequent phrases: {phrases}")

        return "\n".join(lines)

    def get_stats(self) -> str:
        d = self.data
        return (
            f"🧬 Kişilik Evrimi:\n"
            f"  Samimiyet: %{int((1 - d['formality']) * 100)}\n"
            f"  Mizah: %{int(d['humor_frequency'] * 100)}\n"
            f"  İnisiyatif: %{int(d['initiative_level'] * 100)}\n"
            f"  Empati: %{int(d['empathy_level'] * 100)}\n"
            f"  Teknik derinlik: %{int(d['tech_depth'] * 100)}\n"
            f"  Toplam kelime: {d['total_words_exchanged']}\n"
            f"  Espri hit/miss: {d['humor_hits']}/{d['humor_misses']}"
        )
