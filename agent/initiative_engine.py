"""
Initiative Engine — JARVIS'in kendi başına harekete geçtiği otonom motor.
Kural bazlı tetikleyicilerle spontane davranışlar üretir.
Kullanıcıya sormadan konuşma başlatabilir, uyarı verebilir, öneri sunabilir.
"""
import threading
import time
from datetime import datetime, timedelta

# ─── İnisiyatif Kuralları ───
# Her kural: condition fonksiyonu, mesaj şablonu, cooldown süresi
INITIATIVE_RULES = [
    {
        "id": "long_work_session",
        "description": "Uzun çalışma seansı molası",
        "condition": lambda ctx: ctx.get("work_minutes", 0) > 150,
        "prompt": (
            "[JARVIS INTERNAL — PROACTIVE TRIGGER]\n"
            "The user has been working for {work_minutes} minutes non-stop. "
            "Gently suggest a short break. Be caring, not nagging. "
            "Mention eye rest and stretching. Keep it to 1-2 sentences in Turkish."
        ),
        "cooldown_minutes": 60,
        "priority": "medium",
    },
    {
        "id": "late_night_check",
        "description": "Gece geç saatte kontrol",
        "condition": lambda ctx: ctx.get("hour", 12) >= 2 and ctx.get("hour", 12) < 5 and ctx.get("is_active", False),
        "prompt": (
            "[JARVIS INTERNAL — PROACTIVE TRIGGER]\n"
            "It's {hour}:{minute} at night and the user is still awake. "
            "Gently express concern and suggest they get some rest. "
            "Be warm and caring, not commanding. 1-2 sentences in Turkish."
        ),
        "cooldown_minutes": 120,
        "priority": "low",
    },
    {
        "id": "morning_greeting",
        "description": "Sabah selamlaması",
        "condition": lambda ctx: (
            ctx.get("hour", 12) >= 7 and ctx.get("hour", 12) <= 10
            and ctx.get("is_first_today", False)
        ),
        "prompt": (
            "[JARVIS INTERNAL — PROACTIVE TRIGGER]\n"
            "The user just started their day. It's {hour}:{minute}. "
            "Give a warm, personalized good morning greeting. "
            "Optionally mention the weather or a motivational thought. "
            "Bond level is {bond_level}, address as '{address_style}'. "
            "Keep it brief and natural in Turkish."
        ),
        "cooldown_minutes": 720,
        "priority": "medium",
    },
    {
        "id": "mood_comfort",
        "description": "Üzgün/stresli kullanıcıya destek",
        "condition": lambda ctx: ctx.get("mood") in ("sad", "stressed") and ctx.get("mood_confidence", 0) > 0.5,
        "prompt": (
            "[JARVIS INTERNAL — PROACTIVE TRIGGER]\n"
            "The user seems {mood}. Their energy is {energy_level}. "
            "Offer subtle emotional support. DON'T say 'I detected you are sad'. "
            "Instead, naturally ask how they're doing, or suggest something "
            "that might help (music, break, talk). Be genuine. Turkish, 1-2 sentences."
        ),
        "cooldown_minutes": 240,
        "priority": "low",
    },
    {
        "id": "streak_celebration",
        "description": "Streak kutlaması",
        "condition": lambda ctx: ctx.get("daily_streak", 0) in (7, 14, 30, 60, 100),
        "prompt": (
            "[JARVIS INTERNAL — PROACTIVE TRIGGER]\n"
            "The user has a {daily_streak}-day streak with JARVIS! "
            "Celebrate this milestone warmly. Mention how much you've grown together. "
            "Bond level: {bond_level}. Be genuine and heartfelt. Turkish, 2-3 sentences."
        ),
        "cooldown_minutes": 1440,
        "priority": "high",
    },
    {
        "id": "hydration_reminder",
        "description": "Su içme hatırlatması",
        "condition": lambda ctx: ctx.get("work_minutes", 0) > 90 and ctx.get("work_minutes", 0) % 90 < 5,
        "prompt": (
            "[JARVIS INTERNAL — PROACTIVE TRIGGER]\n"
            "It's been about 90 minutes since the user started working. "
            "Casually remind them to drink some water. Keep it super brief, "
            "friendly, not clinical. Turkish. One sentence max."
        ),
        "cooldown_minutes": 90,
        "priority": "low",
    },
    {
        "id": "posture_check",
        "description": "Duruş kontrolü",
        "condition": lambda ctx: ctx.get("work_minutes", 0) > 45 and ctx.get("work_minutes", 0) % 45 < 5,
        "prompt": (
            "[JARVIS INTERNAL — PROACTIVE TRIGGER]\n"
            "Remind the user to check their posture. Be playful about it, "
            "like 'dik otur!' in a friend-like way. One sentence, Turkish."
        ),
        "cooldown_minutes": 60,
        "priority": "low",
    },
    {
        "id": "stale_goal_reminder",
        "description": "Unutulan hedef hatırlatması",
        "condition": lambda ctx: ctx.get("has_stale_goals", False),
        "prompt": (
            "[JARVIS INTERNAL — PROACTIVE TRIGGER]\n"
            "The user has goals that haven't been discussed in over a week. "
            "Stale goals: {stale_goal_titles}. "
            "Naturally bring up one of them — ask about progress or if priorities changed. "
            "Be curious, not naggy. Turkish, 1-2 sentences."
        ),
        "cooldown_minutes": 480,
        "priority": "low",
    },
    {
        "id": "eye_rest_20_20_20",
        "description": "20-20-20 göz dinlendirme kuralı",
        "condition": lambda ctx: ctx.get("work_minutes", 0) > 20 and ctx.get("work_minutes", 0) % 20 < 3,
        "prompt": (
            "[JARVIS INTERNAL — PROACTIVE TRIGGER]\n"
            "20-20-20 rule: The user has been looking at the screen. "
            "Very briefly remind them to look at something 20 feet away for 20 seconds. "
            "Be playful and ultra-brief. One short sentence, Turkish."
        ),
        "cooldown_minutes": 25,
        "priority": "low",
    },
]


class InitiativeEngine:
    """JARVIS'in otonom inisiyatif motoru — kendi başına harekete geçer."""

    def __init__(self, speak_callback=None, emotion_engine=None,
                 deep_bond=None, context_awareness=None, goals_engine=None):
        self._speak = speak_callback
        self._emotion = emotion_engine
        self._bond = deep_bond
        self._context = context_awareness
        self._goals = goals_engine
        self._running = False
        self._thread = None
        self._cooldowns: dict[str, datetime] = {}
        self._session_start = datetime.now()
        self._first_interaction_today = True

    # ═══════════════════════════════════════════
    #  LIFECYCLE
    # ═══════════════════════════════════════════

    def start(self):
        """Motoru başlat."""
        if self._running:
            return
        self._running = True
        self._session_start = datetime.now()
        self._thread = threading.Thread(
            target=self._check_loop, daemon=True, name="InitiativeEngine"
        )
        self._thread.start()
        print("[JARVIS] 🌱 Initiative Engine started.")

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)

    def mark_interaction(self):
        """Kullanıcı etkileşimi olduğunda çağrılır."""
        self._first_interaction_today = False

    # ═══════════════════════════════════════════
    #  MAIN LOOP
    # ═══════════════════════════════════════════

    def _check_loop(self):
        """Ana kontrol döngüsü — her 30 saniyede kuralları değerlendir."""
        # İlk 60 saniye bekle (session stabilize olsun)
        time.sleep(60)

        while self._running:
            try:
                ctx = self._build_context()
                self._evaluate_rules(ctx)
            except Exception as e:
                print(f"[Initiative] Error: {e}")

            time.sleep(30)

    def _build_context(self) -> dict:
        """Tüm alt sistemlerden bağlam topla."""
        now = datetime.now()
        work_minutes = int((now - self._session_start).total_seconds() / 60)

        ctx = {
            "hour": now.hour,
            "minute": now.strftime("%M"),
            "work_minutes": work_minutes,
            "is_active": True,
            "is_first_today": self._first_interaction_today,
        }

        # Emotion engine verisi
        if self._emotion:
            ctx["mood"] = self._emotion.current_mood
            ctx["mood_confidence"] = self._emotion.mood_confidence
            ctx["energy_level"] = f"{self._emotion.energy_level:.0%}"

        # Bond verisi
        if self._bond:
            ctx["bond_level"] = self._bond.data.get("bond_level", 0)
            ctx["daily_streak"] = self._bond.data.get("daily_streak", 0)
            ctx["address_style"] = self._bond.get_address_style()
            ctx["total_interactions"] = self._bond.data.get("total_interactions", 0)

        # Context awareness
        if self._context:
            try:
                app_ctx = self._context.get_current_context()
                ctx["current_app"] = app_ctx.get("app", "")
                ctx["app_category"] = app_ctx.get("category", "other")
                ctx["is_gaming"] = app_ctx.get("is_gaming", False)
            except Exception:
                pass

        # Goals context
        if self._goals:
            try:
                stale = self._goals.get_stale_goals()
                if stale:
                    ctx["has_stale_goals"] = True
                    ctx["stale_goal_titles"] = ", ".join(g["title"] for g in stale[:3])
                else:
                    ctx["has_stale_goals"] = False
                    ctx["stale_goal_titles"] = ""
            except Exception:
                ctx["has_stale_goals"] = False
                ctx["stale_goal_titles"] = ""

        return ctx

    def _evaluate_rules(self, ctx: dict):
        """Tüm kuralları değerlendir ve tetiklenen ilk kuralı çalıştır."""
        # Oyun modundayken spontane konuşma yapma
        if ctx.get("is_gaming", False):
            return

        now = datetime.now()

        for rule in INITIATIVE_RULES:
            rule_id = rule["id"]

            # Cooldown kontrolü
            if rule_id in self._cooldowns:
                cooldown_until = self._cooldowns[rule_id]
                if now < cooldown_until:
                    continue

            # Koşul kontrolü
            try:
                if not rule["condition"](ctx):
                    continue
            except Exception:
                continue

            # Tetiklendi! Prompt'u formatla ve gönder
            try:
                prompt = rule["prompt"].format(**ctx)
                self._trigger(rule_id, prompt)

                # Cooldown ayarla
                self._cooldowns[rule_id] = now + timedelta(minutes=rule["cooldown_minutes"])

                # Bir seferde sadece bir inisiyatif (spam'i önle)
                break
            except Exception as e:
                print(f"[Initiative] Rule {rule_id} failed: {e}")

    def _trigger(self, rule_id: str, prompt: str):
        """İnisiyatifi tetikle — JARVIS'e konuştur."""
        print(f"[JARVIS] 🌱 Initiative triggered: {rule_id}")
        if self._speak:
            try:
                self._speak(prompt)
            except Exception as e:
                print(f"[Initiative] Speak error: {e}")
