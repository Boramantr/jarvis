"""
Screenshot OCR Action — Ekran görüntüsü al ve içindeki metni çıkar.
Kullanım: "Ekrandaki yazıyı oku", "Hata mesajını oku", "Ekranı yakala ve analiz et"
"""
import json
import sys
import tempfile
from datetime import datetime
from pathlib import Path

try:
    import mss
    _MSS = True
except ImportError:
    _MSS = False

try:
    from PIL import Image
    _PIL = True
except ImportError:
    _PIL = False


def _get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent

def _get_api_key() -> str:
    config_path = _get_base_dir() / "config" / "api_keys.json"
    with open(config_path, encoding="utf-8") as f:
        return json.load(f)["gemini_api_key"]


def _capture_screen(monitor_index: int = 0) -> str:
    """Ekran görüntüsü alır, geçici dosyaya kaydeder ve yolunu döner."""
    if not _MSS:
        raise RuntimeError("mss kütüphanesi yüklü değil. pip install mss")

    with mss.mss() as sct:
        monitors = sct.monitors
        if monitor_index + 1 < len(monitors):
            monitor = monitors[monitor_index + 1]
        else:
            monitor = monitors[1] if len(monitors) > 1 else monitors[0]

        screenshot = sct.grab(monitor)

        tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False, prefix="jarvis_ocr_")
        tmp_path = tmp.name
        tmp.close()

        if _PIL:
            img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
            img.save(tmp_path, "PNG")
        else:
            mss.tools.to_png(screenshot.rgb, screenshot.size, output=tmp_path)

    return tmp_path


def _extract_text_with_gemini(image_path: str, request: str = "") -> str:
    """Gemini Vision API ile görüntüden metin çıkarır."""
    import google.generativeai as genai

    genai.configure(api_key=_get_api_key())
    model = genai.GenerativeModel("gemini-2.5-flash")

    img = Image.open(image_path)

    prompt = request if request else (
        "Bu ekran görüntüsündeki tüm metinleri oku ve düzgün formatta listele. "
        "Eğer bir hata mesajı varsa, onu özellikle vurgula."
    )

    response = model.generate_content([prompt, img])
    return response.text.strip()


def screenshot_ocr_action(parameters: dict = None, player=None) -> str:
    params = parameters or {}
    action = params.get("action", "capture_and_read")
    request = params.get("request", "")
    monitor = int(params.get("monitor", 0))

    if player:
        player.write_log("[OCR] Ekran taranıyor...")

    try:
        if action in ("capture_and_read", "read", "ocr"):
            image_path = _capture_screen(monitor)
            try:
                text = _extract_text_with_gemini(image_path, request)
                return text if text else "Ekranda okunabilir bir metin bulunamadı."
            finally:
                try:
                    Path(image_path).unlink(missing_ok=True)
                except Exception:
                    pass

        elif action == "capture":
            screenshots_dir = Path.home() / "Desktop" / "Screenshots"
            screenshots_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = screenshots_dir / f"screenshot_{timestamp}.png"

            tmp_path = _capture_screen(monitor)
            Path(tmp_path).rename(save_path)
            return f"Ekran görüntüsü kaydedildi: {save_path}"

        else:
            return "Geçersiz OCR komutu. Kullanılabilir: capture_and_read, capture"

    except Exception as e:
        return f"OCR hatası: {e}"
