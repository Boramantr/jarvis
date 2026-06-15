"""
Social Graph Engine — JARVIS'in kullanıcının çevresindeki insanları tanımasını sağlar.
İlişkiler, doğum günleri, ilgi alanları ve son konuşulma zamanları takip edilir.
"""
import json
from datetime import datetime, timedelta
from pathlib import Path
from threading import Lock

from memory._jsoncache import invalidate as _invalidate
from memory._jsoncache import load_json_cached

SOCIAL_FILE = Path.home() / ".jarvis" / "memory" / "social_graph.json"
_lock = Lock()


def _empty_graph() -> dict:
    return {"people": {}}


class SocialGraph:
    """Kullanıcının ilişkilerini takip eder."""

    def __init__(self):
        self.data = self._load()

    def _load(self) -> dict:
        d = load_json_cached(SOCIAL_FILE, _empty_graph)
        if isinstance(d, dict) and "people" in d:
            return d
        return _empty_graph()

    def _save(self):
        try:
            SOCIAL_FILE.parent.mkdir(parents=True, exist_ok=True)
            with _lock:
                SOCIAL_FILE.write_text(
                    json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8"
                )
                _invalidate(SOCIAL_FILE)
        except Exception:
            pass

    # ═══════════════════════════════════════════
    #  CRUD
    # ═══════════════════════════════════════════

    def add_person(self, name: str, relationship: str = "arkadaş",
                   birthday: str = None, notes: str = "") -> str:
        """Yeni bir kişi ekle veya güncelle."""
        key = name.lower().strip()
        if key not in self.data["people"]:
            self.data["people"][key] = {
                "name": name,
                "relationship": relationship,
                "birthday": birthday,
                "interests": [],
                "last_mentioned": datetime.now().strftime("%Y-%m-%d"),
                "interaction_count": 1,
                "notes": notes,
                "added_on": datetime.now().strftime("%Y-%m-%d")
            }
            res = f"👤 Kişi eklendi: {name} ({relationship})"
        else:
            p = self.data["people"][key]
            if relationship: p["relationship"] = relationship
            if birthday: p["birthday"] = birthday
            if notes: p["notes"] = notes
            p["last_mentioned"] = datetime.now().strftime("%Y-%m-%d")
            p["interaction_count"] += 1
            res = f"👤 Kişi güncellendi: {name}"

        self._save()
        return res

    def add_interest(self, name: str, interest: str) -> str:
        """Kişiye ilgi alanı ekle."""
        key = name.lower().strip()
        if key in self.data["people"]:
            p = self.data["people"][key]
            if interest not in p["interests"]:
                p["interests"].append(interest)
            p["last_mentioned"] = datetime.now().strftime("%Y-%m-%d")
            p["interaction_count"] += 1
            self._save()
            return f"✅ {name} için ilgi alanı eklendi: {interest}"
        return f"Kişi bulunamadı: {name}. Önce eklemelisin."

    def get_person_info(self, name: str) -> str:
        """Kişi bilgisini getir."""
        key = name.lower().strip()
        if key in self.data["people"]:
            p = self.data["people"][key]
            p["last_mentioned"] = datetime.now().strftime("%Y-%m-%d")
            p["interaction_count"] += 1
            self._save()

            lines = [f"👤 {p['name']} ({p.get('relationship', 'bilinmiyor')})"]
            if p.get("birthday"): lines.append(f"  🎂 Doğum Günü: {p['birthday']}")
            if p.get("interests"): lines.append(f"  ⭐ İlgi Alanları: {', '.join(p['interests'])}")
            if p.get("notes"): lines.append(f"  📝 Notlar: {p['notes']}")
            lines.append(f"  🗣️ Etkileşim: {p['interaction_count']} (Son: {p['last_mentioned']})")
            return "\n".join(lines)
        return f"{name} hakkında bir bilgim yok."

    def list_people(self) -> str:
        """Tüm kişileri listele."""
        if not self.data["people"]:
            return "Henüz rehberimde kimse yok."

        lines = ["👥 Sosyal Ağ:"]
        # En çok etkileşime girilenleri üstte göster
        sorted_people = sorted(
            self.data["people"].values(),
            key=lambda x: x.get("interaction_count", 0),
            reverse=True
        )

        for p in sorted_people[:15]:
            lines.append(f"  - {p['name']} ({p.get('relationship', '?')})")

        if len(sorted_people) > 15:
            lines.append(f"  ...ve {len(sorted_people)-15} kişi daha.")

        return "\n".join(lines)

    # ═══════════════════════════════════════════
    #  QUERIES FOR PROMPT
    # ═══════════════════════════════════════════

    def get_upcoming_birthdays(self, days: int = 14) -> list:
        """Yaklaşan doğum günlerini getir."""
        upcoming = []
        now = datetime.now()
        current_year = now.year

        for p in self.data["people"].values():
            if p.get("birthday"):
                try:
                    # YYYY-MM-DD formatında bekliyoruz, sadece MM-DD kısmını al
                    parts = p["birthday"].split("-")
                    if len(parts) >= 2:
                        m, d = int(parts[-2]), int(parts[-1])
                        # Bu yılki doğum günü
                        bday_this_year = datetime(current_year, m, d)
                        # Eğer bu yıl geçtiyse, seneye bak
                        if (bday_this_year - now).days < -1:
                            bday_this_year = datetime(current_year + 1, m, d)

                        diff = (bday_this_year - now).days
                        if 0 <= diff <= days:
                            upcoming.append((p["name"], diff))
                except Exception:
                    pass

        return upcoming

    def get_stale_relationships(self, days: int = 30) -> list:
        """Uzun süredir konuşulmayan yakın kişileri bul."""
        cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        stale = []

        for p in self.data["people"].values():
            rel = p.get("relationship", "").lower()
            # Sadece yakın ilişkileri uyar
            if rel in ["arkadaş", "aile", "kardeş", "anne", "baba", "sevgili", "eş"]:
                if p.get("last_mentioned", "2000-01-01") < cutoff:
                    stale.append(p["name"])
        return stale

    def get_prompt_context(self) -> str:
        """System prompt'a eklenecek sosyal bağlam."""
        if not self.data["people"]:
            return ""

        lines = ["[SOCIAL CONTEXT]"]

        # En yakın 3 kişi (etkileşime göre)
        sorted_people = sorted(
            self.data["people"].values(),
            key=lambda x: x.get("interaction_count", 0),
            reverse=True
        )
        if sorted_people:
            top_names = ", ".join([p["name"] for p in sorted_people[:3]])
            lines.append(f"  Close contacts: {top_names}")

        birthdays = self.get_upcoming_birthdays()
        if birthdays:
            for name, days in birthdays:
                if days == 0:
                    lines.append(f"  🎂 TODAY is {name}'s birthday! Remind the user to celebrate!")
                else:
                    lines.append(f"  ⏰ {name}'s birthday is in {days} days.")

        stale = self.get_stale_relationships()
        if stale:
            names = ", ".join(stale[:3])
            lines.append(f"  ⚠️ User hasn't mentioned these close contacts recently: {names}")

        return "\n".join(lines)


def social_action(parameters: dict = None, player=None) -> str:
    """Tool olarak çağrılabilir sosyal ağ action'ı."""
    engine = SocialGraph()
    params = parameters or {}
    action = params.get("action", "list")

    if action == "list":
        return engine.list_people()
    elif action == "add":
        name = params.get("name", "")
        if not name: return "İsim gerekli."
        return engine.add_person(
            name=name,
            relationship=params.get("relationship", "arkadaş"),
            birthday=params.get("birthday"),
            notes=params.get("notes", "")
        )
    elif action == "interest":
        name = params.get("name", "")
        interest = params.get("interest", "")
        if not name or not interest: return "İsim ve ilgi alanı gerekli."
        return engine.add_interest(name, interest)
    elif action == "info":
        name = params.get("name", "")
        if not name: return "İsim gerekli."
        return engine.get_person_info(name)
    else:
        return "Kullanılabilir actionlar: list, add, interest, info"
