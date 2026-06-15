"""
Goals Engine — Kullanıcının hayallerini, hedeflerini ve planlarını takip eder.
JARVIS artık ne istediğini bilir ve hatırlatır.
"""
import json
from datetime import datetime, timedelta
from pathlib import Path
from threading import Lock

from memory._jsoncache import invalidate as _invalidate
from memory._jsoncache import load_json_cached

GOALS_FILE = Path.home() / ".jarvis" / "memory" / "goals.json"
_lock = Lock()


def _empty_goals() -> dict:
    return {"goals": [], "completed": [], "daily_micro": None}


class GoalsEngine:
    """Kullanıcının hayallerini ve hedeflerini canlı tutar."""

    def __init__(self):
        self.data = self._load()

    def _load(self) -> dict:
        d = load_json_cached(GOALS_FILE, _empty_goals)
        if isinstance(d, dict):
            for k in _empty_goals():
                if k not in d:
                    d[k] = _empty_goals()[k]
            return d
        return _empty_goals()

    def _save(self):
        try:
            GOALS_FILE.parent.mkdir(parents=True, exist_ok=True)
            self.data["completed"] = self.data["completed"][-30:]
            with _lock:
                GOALS_FILE.write_text(
                    json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8"
                )
                _invalidate(GOALS_FILE)
        except Exception:
            pass

    # ═══════════════════════════════════════════
    #  CRUD
    # ═══════════════════════════════════════════

    def add_goal(self, title: str, category: str = "personal",
                 deadline: str = None, notes: str = "") -> str:
        """Yeni hedef ekle."""
        goal = {
            "id": f"g_{int(datetime.now().timestamp())}",
            "title": title[:200],
            "category": category,
            "created": datetime.now().strftime("%Y-%m-%d"),
            "deadline": deadline,
            "milestones": [],
            "progress": 0.0,
            "last_discussed": datetime.now().strftime("%Y-%m-%d"),
            "notes": notes[:300],
            "status": "active",
        }
        self.data["goals"].append(goal)
        self._save()
        return f"🎯 Hedef eklendi: {title}"

    def add_milestone(self, goal_id: str, task: str) -> str:
        """Hedefe milestone ekle."""
        for g in self.data["goals"]:
            if g["id"] == goal_id:
                g["milestones"].append({
                    "task": task[:150],
                    "status": "pending",
                    "added": datetime.now().strftime("%Y-%m-%d"),
                })
                self._recalc_progress(g)
                self._save()
                return f"✅ Milestone eklendi: {task}"
        return "Hedef bulunamadı."

    def complete_milestone(self, goal_id: str, milestone_index: int) -> str:
        """Milestone'u tamamla."""
        for g in self.data["goals"]:
            if g["id"] == goal_id and milestone_index < len(g["milestones"]):
                g["milestones"][milestone_index]["status"] = "done"
                g["milestones"][milestone_index]["completed"] = datetime.now().strftime("%Y-%m-%d")
                self._recalc_progress(g)
                self._save()
                return f"🎉 Milestone tamamlandı! İlerleme: %{int(g['progress'] * 100)}"
        return "Hedef veya milestone bulunamadı."

    def complete_goal(self, goal_id: str) -> str:
        """Hedefi tamamla."""
        for i, g in enumerate(self.data["goals"]):
            if g["id"] == goal_id:
                g["status"] = "completed"
                g["progress"] = 1.0
                g["completed_date"] = datetime.now().strftime("%Y-%m-%d")
                self.data["completed"].append(self.data["goals"].pop(i))
                self._save()
                return f"🏆 Hedef tamamlandı: {g['title']}!"
        return "Hedef bulunamadı."

    def update_discussed(self, goal_id: str):
        """Son konuşulma tarihini güncelle."""
        for g in self.data["goals"]:
            if g["id"] == goal_id:
                g["last_discussed"] = datetime.now().strftime("%Y-%m-%d")
                self._save()
                return

    def _recalc_progress(self, goal: dict):
        ms = goal.get("milestones", [])
        if not ms:
            return
        done = sum(1 for m in ms if m["status"] == "done")
        goal["progress"] = round(done / len(ms), 2)

    # ═══════════════════════════════════════════
    #  QUERIES
    # ═══════════════════════════════════════════

    def list_goals(self) -> str:
        """Aktif hedefleri listele."""
        goals = [g for g in self.data["goals"] if g["status"] == "active"]
        if not goals:
            return "Henüz aktif hedef yok. Bir hedef eklemek ister misin?"

        lines = ["🎯 Aktif Hedefler:"]
        for g in goals:
            pct = int(g["progress"] * 100)
            bar = "█" * (pct // 10) + "░" * (10 - pct // 10)
            deadline = f" ⏰ {g['deadline']}" if g.get("deadline") else ""
            lines.append(f"  [{g['id']}] {g['title']}")
            lines.append(f"    {bar} {pct}%{deadline} ({g['category']})")
            if g.get("milestones"):
                for j, m in enumerate(g["milestones"]):
                    icon = "✅" if m["status"] == "done" else "⬜"
                    lines.append(f"    {icon} {j}. {m['task']}")
        return "\n".join(lines)

    def get_stale_goals(self, days: int = 7) -> list:
        """Uzun süredir konuşulmayan hedefleri bul."""
        cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        stale = []
        for g in self.data["goals"]:
            if g["status"] == "active" and g.get("last_discussed", "2000-01-01") < cutoff:
                stale.append(g)
        return stale

    def get_upcoming_deadlines(self, days: int = 7) -> list:
        """Yaklaşan deadline'ları bul."""
        upcoming = []
        now = datetime.now()
        for g in self.data["goals"]:
            if g["status"] == "active" and g.get("deadline"):
                try:
                    dl = datetime.strptime(g["deadline"], "%Y-%m-%d")
                    if 0 <= (dl - now).days <= days:
                        upcoming.append((g, (dl - now).days))
                except Exception:
                    pass
        return upcoming

    def get_progress_report(self) -> str:
        """Genel ilerleme raporu."""
        active = [g for g in self.data["goals"] if g["status"] == "active"]
        completed = self.data.get("completed", [])

        if not active and not completed:
            return "Henüz hedef kaydı yok."

        lines = ["📊 Hedef İlerleme Raporu:"]
        lines.append(f"  Aktif: {len(active)} | Tamamlanan: {len(completed)}")

        for g in active:
            pct = int(g["progress"] * 100)
            lines.append(f"  • {g['title']}: %{pct}")

        stale = self.get_stale_goals()
        if stale:
            lines.append(f"\n  ⚠️ {len(stale)} hedef uzun süredir konuşulmadı:")
            for g in stale[:3]:
                lines.append(f"    - {g['title']}")

        upcoming = self.get_upcoming_deadlines()
        if upcoming:
            lines.append("\n  ⏰ Yaklaşan deadline'lar:")
            for g, days in upcoming:
                lines.append(f"    - {g['title']}: {days} gün kaldı!")

        return "\n".join(lines)

    def get_prompt_context(self) -> str:
        """System prompt'a eklenecek hedef bağlamı."""
        active = [g for g in self.data["goals"] if g["status"] == "active"]
        if not active:
            return ""

        lines = ["[USER GOALS — remind naturally when relevant]"]
        for g in active[:5]:
            pct = int(g["progress"] * 100)
            lines.append(f"  • {g['title']} ({g['category']}, {pct}%)")

        stale = self.get_stale_goals()
        if stale:
            lines.append(f"  ⚠ {len(stale)} goal(s) haven't been discussed recently. Gently bring them up.")

        upcoming = self.get_upcoming_deadlines()
        if upcoming:
            for g, days in upcoming[:2]:
                lines.append(f"  ⏰ DEADLINE: {g['title']} in {days} days!")

        return "\n".join(lines)


def goals_action(parameters: dict = None, player=None) -> str:
    """Tool olarak çağrılabilir hedef yönetim action'ı."""
    engine = GoalsEngine()
    params = parameters or {}
    action = params.get("action", "list")

    if action == "list":
        return engine.list_goals()
    elif action == "add":
        title = params.get("title", "")
        if not title:
            return "Hedef başlığı gerekli."
        return engine.add_goal(
            title=title,
            category=params.get("category", "personal"),
            deadline=params.get("deadline"),
            notes=params.get("notes", ""),
        )
    elif action == "milestone":
        return engine.add_milestone(params.get("goal_id", ""), params.get("task", ""))
    elif action == "complete_milestone":
        return engine.complete_milestone(
            params.get("goal_id", ""), int(params.get("index", 0))
        )
    elif action == "complete":
        return engine.complete_goal(params.get("goal_id", ""))
    elif action == "report":
        return engine.get_progress_report()
    else:
        return "Kullanılabilir: list, add, milestone, complete_milestone, complete, report"
