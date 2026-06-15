import time

import keyboard
import pygetwindow as gw


def universal_remote_action(parameters: dict = None, player=None) -> str:
    params = parameters or {}
    action = params.get("action", "")
    value = params.get("value", "5")

    if player: player.write_log(f"[Gelişmiş Kumanda] Aksiyon: {action}")

    try:
        active_window = gw.getActiveWindow()

        if action == "minimize":
            if active_window:
                active_window.minimize()
                return "Pencere simge durumuna küçültüldü efendim."

        elif action == "maximize":
            if active_window:
                active_window.maximize()
                return "Pencere tam ekran yapıldı."

        elif action == "restore":
            if active_window:
                active_window.restore()
                return "Pencere normal boyutuna getirildi."

        elif action in ["play", "pause", "play_pause"]:
            keyboard.send("space")
            return "Oynatma durumu değiştirildi."

        elif action == "next":
            keyboard.send("shift+n")
            keyboard.send("media next track")
            return "Sıradaki medyaya geçildi."

        elif action == "previous":
            keyboard.send("shift+p")
            keyboard.send("media previous track")
            return "Önceki medyaya dönüldü."

        elif action == "seek_forward":
            seconds = int(value) if str(value).isdigit() else 5
            presses = seconds // 5
            for _ in range(presses):
                keyboard.send("right")
                time.sleep(0.01)
            return f"Video {seconds} saniye ileri sarıldı."

        elif action == "seek_backward":
            seconds = int(value) if str(value).isdigit() else 5
            presses = seconds // 5
            for _ in range(presses):
                keyboard.send("left")
                time.sleep(0.01)
            return f"Video {seconds} saniye geri alındı."

        elif action == "mute":
            keyboard.send("volume mute")
            return "Ses kapatıldı/açıldı."

    except Exception as e:
        return f"Kumanda hatası: {e}"

    return "Geçersiz gelişmiş kumanda komutu."
