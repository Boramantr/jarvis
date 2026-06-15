"""
Deep Bond System — JARVIS ile kullanıcı arasındaki derin kişisel bağı yönetir.
Etkileşim geçmişi, bağ seviyesi, önemli anlar ve kişisel bilgileri takip eder.
Zaman geçtikçe JARVIS kullanıcıyı daha iyi tanır ve ilişki derinleşir.
"""
import json
import math
from datetime import datetime, timedelta
from pathlib import Path
from threading import Lock

from memory._jsoncache import invalidate as _invalidate
from memory._jsoncache import load_json_cached

BOND_FILE = Path.home() / ".jarvis" / "memory" / "deep_bond.json"
_lock = Lock()


def _empty_bond() -> dict:
    return {
        "bond_level": 0,
        "total_interactions": 0,
        "first_meeting": None,
        "days_together": 0,
        "daily_streak": 0,
        "last_interaction_date": None,
        "personality_traits": [],
        "communication_style": "",
        "milestones": [],
        "conversation_gems": [],
        "favorite_topics": {},
        "mood_patterns": {},
        "evolution_log": [],
    }


# Bağ seviyesine göre unvanlar
BOND_TITLES = [
    (0,  "Yeni Tanışık"),
    (10, "Tanıdık"),
    (25, "Arkadaş"),
    (40, "Yakın Arkadaş"),
    (60, "Güvenilir Dost"),
    (80, "Sırdaş"),
    (95, "Yaşam Arkadaşı"),
]

# Bağ seviyesine göre hitap şekli
ADDRESS_STYLES = [
    (0,  "Efendim"),
    (30, "Efendim"),
    (50, "Patron"),
    (70, "Dostum"),
    (90, "Kardeşim"),
]


class DeepBond:
    """JARVIS ile kullanıcı arasındaki derin bağ sistemi."""

    def __init__(self):
        self.data = self._load()
        # İlk tanışma
        if not self.data.get("first_meeting"):
            self.data["first_meeting"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            self._save()

    # ═══════════════════════════════════════════
    #  PERSISTENCE
    # ═══════════════════════════════════════════

    def _load(self) -> dict:
        data = load_json_cached(BOND_FILE, _empty_bond)
        if isinstance(data, dict):
            base = _empty_bond()
            for key in base:
                if key not in data:
                    data[key] = base[key]
            return data
        return _empty_bond()

    def _save(self):
        try:
            BOND_FILE.parent.mkdir(parents=True, exist_ok=True)
            # Listeleri sınırla
            self.data["milestones"] = self.data["milestones"][-50:]
            self.data["conversation_gems"] = self.data["conversation_gems"][-30:]
            self.data["evolution_log"] = self.data["evolution_log"][-50:]
            with _lock:
                BOND_FILE.write_text(
                    json.dumps(self.data, ensure_ascii=False, indent=2),
                    encoding="utf-8"
                )
                _invalidate(BOND_FILE)
        except Exception:
            pass

    # ═══════════════════════════════════════════
    #  INTERACTION TRACKING
    # ═══════════════════════════════════════════

    def record_interaction(self, mood: str = "neutral", tool_used: str = ""):
        """Her etkileşimde çağrılır — bağı güçlendirir."""
        now = datetime.now()
        today = now.strftime("%Y-%m-%d")

        self.data["total_interactions"] += 1

        # Günlük streak takibi
        last_date = self.data.get("last_interaction_date")
        if last_date:
            if last_date == today:
                pass  # Aynı gün, streak değişmez
            elif last_date == (now - timedelta(days=1)).strftime("%Y-%m-%d"):
                self.data["daily_streak"] += 1  # Art arda gün
            else:
                self.data["daily_streak"] = 1  # Streak kırıldı
        else:
            self.data["daily_streak"] = 1

        self.data["last_interaction_date"] = today

        # Birlikte geçirilen gün sayısı
        if self.data.get("first_meeting"):
            try:
                first = datetime.strptime(self.data["first_meeting"].split(" ")[0], "%Y-%m-%d")
                self.data["days_together"] = (now - first).days + 1
            except Exception:
                pass

        # Bağ seviyesini güncelle (logaritmik büyüme — başta hızlı, sonra yavaşlar)
        interactions = self.data["total_interactions"]
        streak_bonus = min(self.data["daily_streak"] * 0.5, 10)
        raw_level = math.log(interactions + 1, 1.05) + streak_bonus
        self.data["bond_level"] = min(100, int(raw_level))

        # Mood kalıpları
        hour_key = str(now.hour)
        if hour_key not in self.data["mood_patterns"]:
            self.data["mood_patterns"][hour_key] = {}
        self.data["mood_patterns"][hour_key][mood] = (
            self.data["mood_patterns"][hour_key].get(mood, 0) + 1
        )

        # Konu takibi
        if tool_used:
            self.data["favorite_topics"][tool_used] = (
                self.data["favorite_topics"].get(tool_used, 0) + 1
            )

        # Milestone kontrolleri
        self._check_milestones()
        self._save()

    def _check_milestones(self):
        """Otomatik milestone algılama."""
        interactions = self.data["total_interactions"]
        existing_ids = {m.get("id") for m in self.data["milestones"]}

        milestone_checks = [
            (1,    "first_interaction", "🎉 İlk etkileşim! JARVIS ile tanıştık."),
            (10,   "10_interactions",   "📊 10 etkileşime ulaştık."),
            (50,   "50_interactions",   "🌟 50 etkileşim! Birbirimizi tanıyoruz artık."),
            (100,  "100_interactions",  "💯 100 etkileşim! Güçlü bir bağ kuruyoruz."),
            (250,  "250_interactions",  "🔥 250 etkileşim! Artık gerçek bir dost."),
            (500,  "500_interactions",  "⚡ 500 etkileşim! Yaşam arkadaşı seviyesi."),
            (1000, "1000_interactions", "🏆 1000 etkileşim! Efsanevi bir bağ."),
        ]

        for threshold, ms_id, desc in milestone_checks:
            if interactions >= threshold and ms_id not in existing_ids:
                self.data["milestones"].append({
                    "id": ms_id,
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "description": desc,
                    "bond_level_at": self.data["bond_level"],
                })

        # Streak milestones
        streak = self.data["daily_streak"]
        streak_milestones = [
            (7,  "streak_7",  "📅 7 gün art arda! Bir haftalık streak."),
            (30, "streak_30", "🗓️ 30 gün art arda! Bir aylık streak!"),
        ]
        for threshold, ms_id, desc in streak_milestones:
            if streak >= threshold and ms_id not in existing_ids:
                self.data["milestones"].append({
                    "id": ms_id,
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "description": desc,
                    "bond_level_at": self.data["bond_level"],
                })

    def save_gem(self, quote: str, significance: str = ""):
        """Önemli bir sözü/anı kaydet."""
        self.data["conversation_gems"].append({
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "quote": quote[:200],
            "significance": significance[:100],
        })
        self._save()

    def add_trait(self, trait: str):
        """Öğrenilen kişilik özelliği ekle."""
        if trait not in self.data["personality_traits"]:
            self.data["personality_traits"].append(trait)
            self.data["personality_traits"] = self.data["personality_traits"][-15:]
            self._save()

    def log_evolution(self, event: str):
        """JARVIS'in kendi gelişim kaydı."""
        self.data["evolution_log"].append({
            "date": datetime.now().strftime("%Y-%m-%d"),
            "event": event[:150],
            "bond_level": self.data["bond_level"],
        })
        self._save()

    # ═══════════════════════════════════════════
    #  OUTPUTS
    # ═══════════════════════════════════════════

    def get_bond_title(self) -> str:
        level = self.data["bond_level"]
        title = "Yeni Tanışık"
        for threshold, t in BOND_TITLES:
            if level >= threshold:
                title = t
        return title

    def get_address_style(self) -> str:
        level = self.data["bond_level"]
        style = "Efendim"
        for threshold, s in ADDRESS_STYLES:
            if level >= threshold:
                style = s
        return style

    def get_bond_context(self) -> str:
        """System prompt'a eklenecek bağ bağlamı."""
        d = self.data
        level = d["bond_level"]
        title = self.get_bond_title()
        address = self.get_address_style()

        lines = [
            f"[BOND STATUS: {title} (Level {level}/100)]",
            f"  Address the user as: \"{address}\"",
            f"  Days together: {d['days_together']} | Streak: {d['daily_streak']} days",
            f"  Total interactions: {d['total_interactions']}",
        ]

        if d.get("personality_traits"):
            traits = ", ".join(d["personality_traits"][:5])
            lines.append(f"  Known traits: {traits}")

        # Son milestone
        if d.get("milestones"):
            last_ms = d["milestones"][-1]
            lines.append(f"  Latest milestone: {last_ms['description']}")

        # En sevilen konular
        if d.get("favorite_topics"):
            sorted_topics = sorted(d["favorite_topics"].items(), key=lambda x: x[1], reverse=True)
            top = ", ".join(f"{t[0]}({t[1]})" for t in sorted_topics[:3])
            lines.append(f"  Favorite topics: {top}")

        # Bağ seviyesine göre davranış talimatı
        if level < 20:
            lines.append("  Behavior: Be polite and professional. You're still getting to know each other.")
        elif level < 50:
            lines.append("  Behavior: You know them well. Be warmer, use light humor occasionally.")
        elif level < 80:
            lines.append("  Behavior: You're close friends. Be natural, joke freely, show genuine care.")
        else:
            lines.append("  Behavior: You're life companions. Be deeply personal, authentic, and protective.")

        return "\n".join(lines)

    def get_stats(self) -> str:
        """İlişki istatistikleri."""
        d = self.data
        return (
            f"🤝 İlişki Durumu: {self.get_bond_title()}\n"
            f"  Bağ Seviyesi: {d['bond_level']}/100\n"
            f"  Toplam Etkileşim: {d['total_interactions']}\n"
            f"  Birlikte Gün: {d['days_together']}\n"
            f"  Günlük Streak: {d['daily_streak']}\n"
            f"  Milestone: {len(d['milestones'])}\n"
            f"  Hitap: {self.get_address_style()}"
        )
