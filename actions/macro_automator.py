"""
Macro Automator Action — Klavye ve fare otomasyonu.
Kullanım: "Şu konuma 10 kere tıkla", "Metni yaz" vb.
"""
import threading
import time

try:
    import pyautogui
    _PYAUTO = True
except ImportError:
    _PYAUTO = False

_macro_thread = None
_stop_macro = False

def _run_click_macro(x, y, clicks, interval):
    global _stop_macro
    for i in range(clicks):
        if _stop_macro:
            break
        if x is not None and y is not None:
            pyautogui.click(x=x, y=y)
        else:
            pyautogui.click()
        time.sleep(interval)

def macro_automator_action(parameters: dict = None, player=None) -> str:
    global _macro_thread, _stop_macro

    if not _PYAUTO:
        return "❌ pyautogui kütüphanesi eksik. Lütfen 'pip install pyautogui' ile kurun."

    params = parameters or {}
    action = params.get("action", "status")

    if player:
        player.write_log(f"[Macro] Komut: {action}")

    if action == "stop":
        _stop_macro = True
        return "🛑 Makro işlemi durduruldu."

    elif action == "click_loop":
        x = params.get("x")
        y = params.get("y")
        clicks = int(params.get("clicks", 10))
        interval = float(params.get("interval", 1.0))

        # Stop previous if running
        _stop_macro = True
        if _macro_thread and _macro_thread.is_alive():
            _macro_thread.join(timeout=1.0)

        _stop_macro = False
        _macro_thread = threading.Thread(target=_run_click_macro, args=(x, y, clicks, interval), daemon=True)
        _macro_thread.start()

        msg = f"🖱️ {clicks} kere tıklanacak (Aralık: {interval}sn)."
        if x and y:
            msg += f" Hedef Koordinat: {x}, {y}."
        msg += " Durdurmak isterseniz 'makroyu durdur' demeniz yeterli."
        return msg

    elif action == "type_text":
        text = params.get("text", "")
        interval = float(params.get("interval", 0.05))
        if not text:
            return "❌ Yazılacak metin bulunamadı."

        # Write text after a short delay so user can focus input
        time.sleep(1)
        pyautogui.write(text, interval=interval)
        return "⌨️ Metin başarıyla yazıldı."

    elif action == "press_key":
        key = params.get("key", "enter")
        times = int(params.get("times", 1))

        time.sleep(1)
        for _ in range(times):
            pyautogui.press(key)
        return f"⌨️ '{key}' tuşuna {times} kez basıldı."

    elif action == "get_position":
        x, y = pyautogui.position()
        return f"📍 Farenin şu anki konumu: X={x}, Y={y}"

    elif action == "status":
        return (
            "🤖 Makro Otomasyonu Araçları:\n"
            "  • click_loop — Belirli aralıklarla otomatik tıklar\n"
            "  • type_text  — Belirli bir metni yazar\n"
            "  • press_key  — Bir tuşa basar (enter, space vb.)\n"
            "  • get_position — Farenin anlık koordinatını söyler\n"
            "  • stop       — Devam eden makroyu durdurur"
        )

    return "Geçersiz komut. Kullanılabilir: click_loop, type_text, press_key, get_position, stop, status"
