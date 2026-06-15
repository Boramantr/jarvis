"""
Brightness Control Action — Ekran parlaklığını ayarla.
Kullanım: "Parlaklığı %30'a düşür", "Parlaklığı artır", "Parlaklık kaç?"
"""
import platform
import subprocess

_SYSTEM = platform.system()


def _get_brightness_windows() -> int:
    """Windows'ta mevcut parlaklığı al."""
    try:
        result = subprocess.run(
            ["powershell", "-Command",
             "(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightness).CurrentBrightness"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0 and result.stdout.strip():
            return int(result.stdout.strip())
    except Exception:
        pass

    try:
        import wmi
        c = wmi.WMI(namespace='wmi')
        methods = c.WmiMonitorBrightness()
        if methods:
            return methods[0].CurrentBrightness
    except Exception:
        pass

    return -1


def _set_brightness_windows(level: int) -> bool:
    """Windows'ta parlaklığı ayarla."""
    level = max(0, min(100, level))

    try:
        result = subprocess.run(
            ["powershell", "-Command",
             f"(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,{level})"],
            capture_output=True, text=True, timeout=10
        )
        return result.returncode == 0
    except Exception:
        pass

    try:
        import wmi
        c = wmi.WMI(namespace='wmi')
        methods = c.WmiMonitorBrightnessMethods()
        if methods:
            methods[0].WmiSetBrightness(level, 0)
            return True
    except Exception:
        pass

    return False


def brightness_control_action(parameters: dict = None, player=None) -> str:
    params = parameters or {}
    action = params.get("action", "get")
    value = params.get("value", "")

    if player:
        player.write_log(f"[Brightness] Komut: {action}")

    if _SYSTEM != "Windows":
        return "Parlaklık kontrolü şu an sadece Windows'ta destekleniyor efendim."

    if action == "get":
        current = _get_brightness_windows()
        if current >= 0:
            return f"🔆 Mevcut parlaklık: %{current}"
        return "Parlaklık değeri okunamadı efendim. Masaüstü monitörlerde bu özellik çalışmayabilir."

    elif action == "set":
        try:
            level = int(value)
        except (ValueError, TypeError):
            return "Parlaklık değeri belirtin (0-100)."

        level = max(0, min(100, level))
        if _set_brightness_windows(level):
            emoji = "🔆" if level > 60 else "🔅" if level > 20 else "🌑"
            return f"{emoji} Parlaklık %{level} olarak ayarlandı efendim."
        return "Parlaklık ayarlanamadı. Masaüstü monitörlerde bu özellik çalışmayabilir."

    elif action == "up":
        current = _get_brightness_windows()
        if current < 0:
            current = 50
        new_level = min(100, current + 15)
        if _set_brightness_windows(new_level):
            return f"🔆 Parlaklık artırıldı: %{new_level}"
        return "Parlaklık artırılamadı."

    elif action == "down":
        current = _get_brightness_windows()
        if current < 0:
            current = 50
        new_level = max(0, current - 15)
        if _set_brightness_windows(new_level):
            return f"🔅 Parlaklık düşürüldü: %{new_level}"
        return "Parlaklık düşürülemedi."

    elif action == "dim":
        if _set_brightness_windows(10):
            return "🌑 Ekran kısıldı (%10)."
        return "Ekran kısılamadı."

    elif action == "max":
        if _set_brightness_windows(100):
            return "🔆 Ekran maksimum parlaklığa ayarlandı."
        return "Parlaklık ayarlanamadı."

    return "Geçersiz parlaklık komutu. Kullanılabilir: get, set, up, down, dim, max"
