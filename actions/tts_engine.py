"""
TTS Engine Action — Metin-konuşma dönüştürücü.
Kullanım: "Bu metni sesli oku", "Panodaki metni oku", "Ses dosyası olarak kaydet"
"""
import os
import sys
import threading
from pathlib import Path

_TTS_ENGINE = None
_TTS_LOCK = threading.Lock()

def _get_engine():
    """pyttsx3 engine'i lazy-load et."""
    global _TTS_ENGINE
    if _TTS_ENGINE is None:
        try:
            import pyttsx3
            _TTS_ENGINE = pyttsx3.init()
            _TTS_ENGINE.setProperty("rate", 170)  # Normal hız
            _TTS_ENGINE.setProperty("volume", 0.9)
        except Exception:
            return None
    return _TTS_ENGINE


def _get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


def tts_engine_action(parameters: dict = None, player=None) -> str:
    params = parameters or {}
    action = params.get("action", "speak")

    if player:
        player.write_log(f"[TTS] Komut: {action}")

    if action == "speak":
        text = params.get("text", "")
        if not text:
            return "❌ Okunacak metin belirtilmedi."

        language = params.get("language", "tr").lower()

        # Önce pyttsx3 dene (offline)
        with _TTS_LOCK:
            engine = _get_engine()
            if engine:
                try:
                    # Mevcut seslerde dil kontrolü
                    voices = engine.getProperty("voices")
                    for voice in voices:
                        if language in voice.id.lower() or language in str(voice.languages).lower():
                            engine.setProperty("voice", voice.id)
                            break

                    engine.say(text)
                    engine.runAndWait()
                    return f"🔊 Metin okundu ({len(text)} karakter, dil: {language})"
                except Exception:
                    pass

        # Fallback: gTTS ile MP3 oluştur ve çal
        try:
            import tempfile

            from gtts import gTTS

            tts = gTTS(text=text, lang=language)
            temp_dir = _get_base_dir() / "memory"
            temp_dir.mkdir(parents=True, exist_ok=True)
            temp_file = temp_dir / "tts_output.mp3"
            tts.save(str(temp_file))
            os.startfile(str(temp_file))
            return f"🔊 Metin okunuyor ({len(text)} karakter, dil: {language})"
        except ImportError:
            return "❌ TTS kütüphanesi bulunamadı. pip install pyttsx3 veya pip install gTTS"
        except Exception as e:
            return f"❌ TTS hatası: {e}"

    elif action == "read_clipboard":
        try:
            import pyperclip
            text = pyperclip.paste()
            if not text:
                return "❌ Pano boş."

            # Recursive call
            return tts_engine_action({"action": "speak", "text": text, "language": params.get("language", "tr")}, player)
        except ImportError:
            return "❌ pyperclip kütüphanesi gerekli."

    elif action == "read_file":
        file_path = params.get("file_path", "")
        if not file_path:
            return "❌ Dosya yolu belirtilmedi."

        try:
            path = Path(file_path)
            if not path.exists():
                return f"❌ Dosya bulunamadı: {file_path}"

            text = path.read_text(encoding="utf-8")
            if len(text) > 5000:
                text = text[:5000]
                truncated = True
            else:
                truncated = False

            result = tts_engine_action({"action": "speak", "text": text, "language": params.get("language", "tr")}, player)
            if truncated:
                result += "\n⚠️ Dosya çok uzun, ilk 5000 karakter okundu."
            return result
        except Exception as e:
            return f"❌ Dosya okuma hatası: {e}"

    elif action == "save_audio":
        text = params.get("text", "")
        output = params.get("output_path", "")
        language = params.get("language", "tr").lower()

        if not text:
            return "❌ Metin belirtilmedi."

        if not output:
            output = str(_get_base_dir() / "memory" / f"tts_{language}.mp3")

        try:
            from gtts import gTTS
            tts = gTTS(text=text, lang=language)
            tts.save(output)
            return f"💾 Ses dosyası kaydedildi: {output} ({len(text)} karakter)"
        except ImportError:
            # pyttsx3 ile kaydet
            with _TTS_LOCK:
                engine = _get_engine()
                if engine:
                    try:
                        engine.save_to_file(text, output.replace(".mp3", ".wav"))
                        engine.runAndWait()
                        return f"💾 Ses dosyası kaydedildi: {output.replace('.mp3', '.wav')}"
                    except Exception as e:
                        return f"❌ Kaydetme hatası: {e}"
            return "❌ gTTS kütüphanesi gerekli. pip install gTTS"
        except Exception as e:
            return f"❌ Kaydetme hatası: {e}"

    elif action == "speed":
        rate_map = {"slow": 120, "yavaş": 120, "normal": 170, "fast": 220, "hızlı": 220}
        rate = params.get("rate", "normal").lower()
        wpm = rate_map.get(rate, 170)

        with _TTS_LOCK:
            engine = _get_engine()
            if engine:
                engine.setProperty("rate", wpm)
                return f"🔊 Okuma hızı ayarlandı: {rate} ({wpm} WPM)"
        return "❌ TTS engine başlatılamadı."

    elif action == "list_voices":
        with _TTS_LOCK:
            engine = _get_engine()
            if not engine:
                return "❌ TTS engine başlatılamadı."

            voices = engine.getProperty("voices")
            lines = [f"🎤 Mevcut Sesler ({len(voices)} adet):"]
            for i, voice in enumerate(voices):
                name = voice.name
                lang = ",".join(voice.languages) if voice.languages else "?"
                lines.append(f"  {i+1}. {name} ({lang})")
            return "\n".join(lines)

    elif action == "set_voice":
        voice_name = params.get("voice_name", "")
        with _TTS_LOCK:
            engine = _get_engine()
            if not engine:
                return "❌ TTS engine başlatılamadı."

            voices = engine.getProperty("voices")
            for voice in voices:
                if voice_name.lower() in voice.name.lower():
                    engine.setProperty("voice", voice.id)
                    return f"🎤 Ses değiştirildi: {voice.name}"
            return f"❌ '{voice_name}' adlı ses bulunamadı."

    return "Geçersiz komut. Kullanılabilir: speak, read_clipboard, read_file, save_audio, speed, list_voices, set_voice"
