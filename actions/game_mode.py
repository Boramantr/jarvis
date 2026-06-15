"""
Game Mode Action — Oyun modu: DND, performans boost, otomatik oyun algılama.
Kullanım: "Oyun modunu aç", "Performans boost", "Oyun seansı özeti"
"""
import os
import subprocess
import time

try:
    import psutil
    _PSUTIL = True
except ImportError:
    _PSUTIL = False

try:
    import pygetwindow as gw
    _GW = True
except ImportError:
    _GW = False


# Bilinen oyun process isimleri
KNOWN_GAMES = {
    "VALORANT-Win64-Shipping.exe": "Valorant",
    "csgo.exe": "CS:GO",
    "cs2.exe": "CS2",
    "LeagueClient.exe": "League of Legends",
    "League of Legends.exe": "League of Legends",
    "FortniteClient-Win64-Shipping.exe": "Fortnite",
    "javaw.exe": "Minecraft",
    "Minecraft.Windows.exe": "Minecraft",
    "TslGame.exe": "PUBG",
    "GTA5.exe": "GTA V",
    "FiveM.exe": "FiveM",
    "RocketLeague.exe": "Rocket League",
    "r5apex.exe": "Apex Legends",
    "Overwatch.exe": "Overwatch 2",
    "RainbowSix.exe": "Rainbow Six Siege",
    "EscapeFromTarkov.exe": "Escape from Tarkov",
    "Cyberpunk2077.exe": "Cyberpunk 2077",
    "eldenring.exe": "Elden Ring",
    "Roblox": "Roblox",
    "FIFA": "FIFA",
    "NBA2K": "NBA 2K",
}

# Kapatılabilir gereksiz processler
CLOSEABLE_PROCESSES = [
    "OneDrive.exe",
    "Teams.exe",
    "Slack.exe",
    "Skype.exe",
    "YourPhone.exe",
    "PhoneExperienceHost.exe",
    "SearchUI.exe",
    "cortana.exe",
    "GameBarPresenceWriter.exe",
]

_game_mode_active = False
_game_session_start = None
_detected_game = None


def _detect_running_game() -> str | None:
    """Çalışan bir oyun var mı kontrol et."""
    if not _PSUTIL:
        return None

    try:
        for proc in psutil.process_iter(["name"]):
            try:
                name = proc.info["name"]
                if name in KNOWN_GAMES:
                    return KNOWN_GAMES[name]
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
    except Exception:
        pass

    # Pencere başlığından algıla
    if _GW:
        try:
            active = gw.getActiveWindow()
            if active:
                for key, game in KNOWN_GAMES.items():
                    if key.lower().replace(".exe", "") in active.title.lower():
                        return game
        except Exception:
            pass

    return None


def _kill_unnecessary() -> int:
    """Gereksiz arka plan processlerini kapat."""
    killed = 0
    for proc_name in CLOSEABLE_PROCESSES:
        try:
            result = os.system(f'taskkill /F /IM "{proc_name}" /T 2>nul')
            if result == 0:
                killed += 1
        except Exception:
            pass
    return killed


def _set_high_performance() -> bool:
    """Yüksek performans güç planını aktifle."""
    try:
        # Yüksek performans GUID
        result = subprocess.run(
            ["powershell", "-Command",
             "powercfg /setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"],
            capture_output=True, text=True, timeout=5
        )
        return result.returncode == 0
    except Exception:
        return False


def _set_balanced_power() -> bool:
    """Dengeli güç planına geri dön."""
    try:
        result = subprocess.run(
            ["powershell", "-Command",
             "powercfg /setactive 381b4222-f694-41f0-9685-ff5bb260df2e"],
            capture_output=True, text=True, timeout=5
        )
        return result.returncode == 0
    except Exception:
        return False


def game_mode_action(parameters: dict = None, player=None) -> str:
    global _game_mode_active, _game_session_start, _detected_game

    params = parameters or {}
    action = params.get("action", "status")

    if player:
        player.write_log(f"[GameMode] Komut: {action}")

    if action in ("activate", "on", "aç"):
        if _game_mode_active:
            return "Oyun modu zaten aktif efendim."

        _game_mode_active = True
        _game_session_start = time.time()
        _detected_game = _detect_running_game()

        results = ["🎮 Oyun Modu Aktifleştirildi!"]

        # Performans boost
        killed = _kill_unnecessary()
        if killed:
            results.append(f"  🗑️ {killed} gereksiz process kapatıldı")

        if _set_high_performance():
            results.append("  ⚡ Yüksek performans modu aktif")

        if _detected_game:
            results.append(f"  🎯 Algılanan oyun: {_detected_game}")

        results.append("  🔇 Sadece acil bildirimler aktif")
        results.append("  İyi oyunlar efendim! GG!")

        return "\n".join(results)

    elif action in ("deactivate", "off", "kapat"):
        if not _game_mode_active:
            return "Oyun modu zaten kapalı."

        _game_mode_active = False

        results = ["🎮 Oyun Modu Kapatıldı"]

        _set_balanced_power()
        results.append("  ⚡ Dengeli güç planına dönüldü")

        if _game_session_start:
            duration = (time.time() - _game_session_start) / 60
            hours = int(duration // 60)
            mins = int(duration % 60)
            results.append(f"  ⏱️ Oyun süresi: {hours}s {mins}dk")
            if _detected_game:
                results.append(f"  🎯 Oynanan: {_detected_game}")
            _game_session_start = None
            _detected_game = None

        return "\n".join(results)

    elif action in ("auto_detect", "detect"):
        game = _detect_running_game()
        if game:
            return f"🎮 Algılanan oyun: {game}. Oyun modunu açmamı ister misiniz?"
        return "Şu anda çalışan bir oyun algılanamadı."

    elif action == "performance_boost":
        results = ["⚡ Performans Boost:"]
        killed = _kill_unnecessary()
        results.append(f"  🗑️ {killed} gereksiz process kapatıldı")

        if _set_high_performance():
            results.append("  ⚡ Yüksek performans modu aktif")

        if _PSUTIL:
            try:
                ram = psutil.virtual_memory()
                results.append(f"  🧠 Mevcut RAM: {ram.available // (1024**2)} MB boş")
            except Exception:
                pass

        return "\n".join(results)

    elif action == "status":
        if _game_mode_active:
            duration = (time.time() - _game_session_start) / 60 if _game_session_start else 0
            game = _detected_game or "Bilinmiyor"
            return (
                f"🎮 Oyun Modu: AKTİF\n"
                f"  Oyun: {game}\n"
                f"  Süre: {int(duration)} dk"
            )
        return "🎮 Oyun Modu: KAPALI"

    elif action == "session_summary":
        if _game_session_start:
            duration = (time.time() - _game_session_start) / 60
            return (
                f"🎮 Mevcut Oyun Seansı:\n"
                f"  Oyun: {_detected_game or 'Bilinmiyor'}\n"
                f"  Süre: {int(duration)} dk\n"
                f"  Mod: {'Aktif' if _game_mode_active else 'Pasif'}"
            )
        return "Aktif bir oyun seansı yok."

    return "Geçersiz oyun modu komutu. Kullanılabilir: activate, deactivate, auto_detect, performance_boost, status, session_summary"
