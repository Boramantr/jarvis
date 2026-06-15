"""
Context Awareness — Aktif pencere takibi ve bağlam farkındalığı.
Hangi uygulamada olduğunu anlar ve JARVIS'in davranışını ayarlar.
"""
import threading
import time
from datetime import datetime

try:
    import pygetwindow as gw
    _GW = True
except ImportError:
    _GW = False

try:
    import psutil
    _PSUTIL = True
except ImportError:
    _PSUTIL = False


# Bilinen uygulama kategorileri
APP_CATEGORIES = {
    # Kodlama
    "code": "coding", "Code": "coding", "Visual Studio": "coding",
    "PyCharm": "coding", "IntelliJ": "coding", "Cursor": "coding",
    "Sublime": "coding", "Atom": "coding", "Vim": "coding",
    "Neovim": "coding", "WebStorm": "coding",

    # Oyun
    "Valorant": "gaming", "Counter-Strike": "gaming", "CS2": "gaming",
    "Minecraft": "gaming", "Fortnite": "gaming", "League of Legends": "gaming",
    "PUBG": "gaming", "Apex Legends": "gaming", "Overwatch": "gaming",
    "Steam": "gaming", "Epic Games": "gaming", "Roblox": "gaming",
    "GTA": "gaming", "FIFA": "gaming", "Rocket League": "gaming",

    # Medya
    "Spotify": "media", "VLC": "media", "Netflix": "media",
    "YouTube": "media", "Twitch": "media", "Disney": "media",

    # İletişim
    "Discord": "communication", "WhatsApp": "communication",
    "Telegram": "communication", "Slack": "communication",
    "Teams": "communication", "Zoom": "communication",

    # Üretkenlik
    "Word": "productivity", "Excel": "productivity", "PowerPoint": "productivity",
    "Notion": "productivity", "Obsidian": "productivity",
    "OneNote": "productivity", "Google Docs": "productivity",

    # Tasarım
    "Figma": "design", "Photoshop": "design", "Illustrator": "design",
    "Blender": "design", "Premiere": "design", "After Effects": "design",

    # Tarayıcı
    "Chrome": "browser", "Firefox": "browser", "Edge": "browser",
    "Brave": "browser", "Opera": "browser", "Safari": "browser",
}


class ContextAwareness:
    """Aktif pencereyi izler ve bağlam sağlar."""

    def __init__(self):
        self._running = False
        self._thread = None
        self._current_app = ""
        self._current_category = "unknown"
        self._app_sessions = {}  # {app: {"start": datetime, "total_seconds": float}}
        self._session_start = datetime.now()
        self._on_change_callback = None

    def _detect_category(self, window_title: str) -> str:
        """Pencere başlığından kategori belirle."""
        for keyword, category in APP_CATEGORIES.items():
            if keyword.lower() in window_title.lower():
                return category
        return "other"

    def _extract_app_name(self, window_title: str) -> str:
        """Pencere başlığından uygulama adını çıkar."""
        if not window_title:
            return "Unknown"

        # Genellikle "dosya - uygulama" formatında
        parts = window_title.split(" - ")
        if len(parts) > 1:
            return parts[-1].strip()

        parts = window_title.split(" — ")
        if len(parts) > 1:
            return parts[-1].strip()

        return window_title.split()[0] if window_title.split() else "Unknown"

    def _track_time(self, app_name: str):
        """Uygulama süresini takip et."""
        now = datetime.now()
        if app_name not in self._app_sessions:
            self._app_sessions[app_name] = {"start": now, "total_seconds": 0}

        session = self._app_sessions[app_name]
        if self._current_app == app_name:
            elapsed = (now - session["start"]).total_seconds()
            session["total_seconds"] += elapsed
        session["start"] = now

    def _monitor_loop(self):
        """Ana izleme döngüsü."""
        while self._running:
            try:
                if _GW:
                    active = gw.getActiveWindow()
                    if active and active.title:
                        title = active.title
                        app = self._extract_app_name(title)
                        category = self._detect_category(title)

                        old_app = self._current_app
                        self._current_app = app
                        self._current_category = category

                        self._track_time(app)

                        # Uygulama değişti callback
                        if app != old_app and self._on_change_callback:
                            try:
                                self._on_change_callback(app, category, title)
                            except Exception:
                                pass
            except Exception:
                pass

            time.sleep(10)  # Her 10 saniyede kontrol — uygulama değişimi için yeterli, CPU/RAM tasarrufu

    def start(self, on_change=None):
        """İzlemeyi başlat."""
        if self._running:
            return
        self._running = True
        self._on_change_callback = on_change
        self._thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True,
            name="ContextAwareness"
        )
        self._thread.start()

    def stop(self):
        self._running = False

    def get_current_context(self) -> dict:
        """Mevcut bağlamı döndür."""
        return {
            "app": self._current_app,
            "category": self._current_category,
            "is_gaming": self._current_category == "gaming",
            "is_coding": self._current_category == "coding",
            "is_media": self._current_category == "media",
        }

    def get_context_for_prompt(self) -> str:
        """Prompt'a eklenecek bağlam."""
        ctx = self.get_current_context()
        if not ctx["app"]:
            return ""

        lines = ["[ACTIVE CONTEXT]"]
        lines.append(f"  Current app: {ctx['app']} (category: {ctx['category']})")

        if ctx["is_gaming"]:
            lines.append("  User is gaming. Be minimal and non-intrusive.")
        elif ctx["is_coding"]:
            lines.append("  User is coding. Be technical and concise.")
        elif ctx["is_media"]:
            lines.append("  User is watching/listening to media.")

        return "\n".join(lines)

    def get_usage_report(self) -> str:
        """Uygulama kullanım raporu."""
        if not self._app_sessions:
            return "Henüz kullanım verisi yok."

        sorted_apps = sorted(
            self._app_sessions.items(),
            key=lambda x: x[1]["total_seconds"],
            reverse=True
        )

        lines = ["📊 Uygulama Kullanım Süresi:"]
        for app, data in sorted_apps[:10]:
            total = data["total_seconds"]
            if total < 60:
                time_str = f"{int(total)}sn"
            elif total < 3600:
                time_str = f"{int(total // 60)}dk"
            else:
                time_str = f"{int(total // 3600)}s {int((total % 3600) // 60)}dk"
            lines.append(f"  {app}: {time_str}")

        return "\n".join(lines)


def context_awareness_action(parameters: dict = None, player=None) -> str:
    """Tool olarak çağrılabilir context awareness action'ı."""
    params = parameters or {}
    action = params.get("action", "status")

    if action == "status":
        if _GW:
            try:
                active = gw.getActiveWindow()
                if active:
                    return f"🖥️ Aktif Pencere: {active.title}"
            except Exception:
                pass
        return "Aktif pencere bilgisi alınamadı."

    elif action == "list_windows":
        if _GW:
            try:
                windows = gw.getAllTitles()
                windows = [w for w in windows if w.strip()]
                if not windows:
                    return "Açık pencere bulunamadı."
                lines = ["🪟 Açık Pencereler:"]
                for i, w in enumerate(windows[:15], 1):
                    lines.append(f"  {i}. {w[:60]}")
                return "\n".join(lines)
            except Exception:
                pass
        return "Pencere listesi alınamadı."

    return "Kullanılabilir: status, list_windows"
