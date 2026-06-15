"""
Volume Mixer Action — Uygulama bazlı ses kontrolü.
Kullanım: "Discord sesini kıs", "Spotify sesini aç", "Tüm sesleri göster"
"""
import platform

_SYSTEM = platform.system()

try:
    from ctypes import POINTER, cast

    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume, ISimpleAudioVolume
    _PYCAW = True
except ImportError:
    _PYCAW = False


APP_NAME_MAP = {
    "chrome": "chrome.exe",
    "google chrome": "chrome.exe",
    "firefox": "firefox.exe",
    "edge": "msedge.exe",
    "spotify": "Spotify.exe",
    "discord": "Discord.exe",
    "vlc": "vlc.exe",
    "steam": "steam.exe",
    "teams": "Teams.exe",
    "zoom": "Zoom.exe",
    "telegram": "Telegram.exe",
    "whatsapp": "WhatsApp.exe",
    "obs": "obs64.exe",
    "brave": "brave.exe",
    "valorant": "VALORANT-Win64-Shipping.exe",
    "cs2": "cs2.exe",
    "minecraft": "javaw.exe",
}


def _resolve_app_name(name: str) -> str:
    """Uygulama adını process adına çevir."""
    key = name.lower().strip()
    if key in APP_NAME_MAP:
        return APP_NAME_MAP[key]
    if not key.endswith(".exe"):
        return key + ".exe"
    return key


def _get_all_sessions() -> list[dict]:
    """Tüm ses oturumlarını listele."""
    if not _PYCAW:
        return []

    sessions_info = []
    try:
        sessions = AudioUtilities.GetAllSessions()
        for session in sessions:
            if session.Process:
                volume = session._ctl.QueryInterface(ISimpleAudioVolume)
                sessions_info.append({
                    "name": session.Process.name(),
                    "pid": session.Process.pid,
                    "volume": round(volume.GetMasterVolume() * 100),
                    "muted": volume.GetMute(),
                    "_volume_ctl": volume,
                })
    except Exception:
        pass
    return sessions_info


def _find_session(app_name: str):
    """Belirli bir uygulamanın ses oturumunu bul."""
    if not _PYCAW:
        return None

    target = _resolve_app_name(app_name).lower()
    try:
        sessions = AudioUtilities.GetAllSessions()
        for session in sessions:
            if session.Process and session.Process.name().lower() == target:
                return session._ctl.QueryInterface(ISimpleAudioVolume)
    except Exception:
        pass
    return None


def _get_master_volume():
    """Ana sistem sesi kontrolü."""
    if not _PYCAW:
        return None
    try:
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        return cast(interface, POINTER(IAudioEndpointVolume))
    except Exception:
        return None


def volume_mixer_action(parameters: dict = None, player=None) -> str:
    params = parameters or {}
    action = params.get("action", "list")
    app = params.get("app", "")
    value = params.get("value", "")

    if player:
        player.write_log(f"[VolumeMixer] {action}: {app}")

    if not _PYCAW:
        return "pycaw kütüphanesi yüklü değil. pip install pycaw"

    if _SYSTEM != "Windows":
        return "Volume mixer şu an sadece Windows'ta destekleniyor."

    if action == "list":
        sessions = _get_all_sessions()
        if not sessions:
            return "Aktif ses oturumu bulunamadı."

        lines = ["🔊 Aktif Ses Oturumları:"]
        for s in sessions:
            mute_icon = "🔇" if s["muted"] else "🔊"
            lines.append(f"  {mute_icon} {s['name']}: %{s['volume']}")
        return "\n".join(lines)

    elif action == "set":
        if not app:
            return "Uygulama adı belirtin efendim."
        try:
            level = int(value)
        except (ValueError, TypeError):
            return "Ses seviyesi belirtin (0-100)."

        level = max(0, min(100, level))
        vol = _find_session(app)
        if vol:
            vol.SetMasterVolume(level / 100.0, None)
            return f"🎚️ {app} sesi %{level} olarak ayarlandı."
        return f"'{app}' uygulaması ses oturumlarında bulunamadı."

    elif action == "mute":
        if not app:
            return "Hangi uygulamayı sessize alayım?"
        vol = _find_session(app)
        if vol:
            vol.SetMute(1, None)
            return f"🔇 {app} sessize alındı."
        return f"'{app}' bulunamadı."

    elif action == "unmute":
        if not app:
            return "Hangi uygulamanın sesini açayım?"
        vol = _find_session(app)
        if vol:
            vol.SetMute(0, None)
            return f"🔊 {app} sesi açıldı."
        return f"'{app}' bulunamadı."

    elif action == "up":
        if not app:
            return "Hangi uygulamanın sesini artırayım?"
        vol = _find_session(app)
        if vol:
            current = vol.GetMasterVolume()
            new_vol = min(1.0, current + 0.15)
            vol.SetMasterVolume(new_vol, None)
            return f"🔊 {app} sesi artırıldı: %{int(new_vol * 100)}"
        return f"'{app}' bulunamadı."

    elif action == "down":
        if not app:
            return "Hangi uygulamanın sesini kısayım?"
        vol = _find_session(app)
        if vol:
            current = vol.GetMasterVolume()
            new_vol = max(0.0, current - 0.15)
            vol.SetMasterVolume(new_vol, None)
            return f"🔉 {app} sesi kısıldı: %{int(new_vol * 100)}"
        return f"'{app}' bulunamadı."

    elif action == "master_set":
        try:
            level = int(value)
        except (ValueError, TypeError):
            return "Ses seviyesi belirtin (0-100)."
        master = _get_master_volume()
        if master:
            master.SetMasterVolumeLevelScalar(max(0, min(100, level)) / 100.0, None)
            return f"🔊 Ana sistem sesi %{level} olarak ayarlandı."
        return "Ana ses kontrolü bulunamadı."

    elif action == "master_mute":
        master = _get_master_volume()
        if master:
            master.SetMute(1, None)
            return "🔇 Sistem sesi kapatıldı."
        return "Ana ses kontrolü bulunamadı."

    elif action == "master_unmute":
        master = _get_master_volume()
        if master:
            master.SetMute(0, None)
            return "🔊 Sistem sesi açıldı."
        return "Ana ses kontrolü bulunamadı."

    return "Geçersiz ses komutu. Kullanılabilir: list, set, mute, unmute, up, down, master_set"
