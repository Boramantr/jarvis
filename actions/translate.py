"""
Translate Action — Anlık çeviri (herhangi bir dil çifti).
Kullanım: "Bunu İngilizce'ye çevir", "Japonca'da teşekkürler nasıl denir"
"""
import json
import sys
from pathlib import Path


def _get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


def _get_api_key() -> str:
    config_path = _get_base_dir() / "config" / "api_keys.json"
    with open(config_path, encoding="utf-8") as f:
        return json.load(f)["gemini_api_key"]


LANGUAGE_MAP = {
    "tr": "Turkish", "en": "English", "de": "German", "fr": "French",
    "es": "Spanish", "it": "Italian", "pt": "Portuguese", "ru": "Russian",
    "ja": "Japanese", "ko": "Korean", "zh": "Chinese", "ar": "Arabic",
    "hi": "Hindi", "nl": "Dutch", "sv": "Swedish", "pl": "Polish",
    "el": "Greek", "cs": "Czech", "ro": "Romanian", "hu": "Hungarian",
    "türkçe": "Turkish", "ingilizce": "English", "almanca": "German",
    "fransızca": "French", "ispanyolca": "Spanish", "italyanca": "Italian",
    "portekizce": "Portuguese", "rusça": "Russian", "japonca": "Japanese",
    "korece": "Korean", "çince": "Chinese", "arapça": "Arabic",
    "hintçe": "Hindi", "felemenkçe": "Dutch", "lehçe": "Polish",
    "yunanca": "Greek",
}


def _resolve_language(lang_input: str) -> str:
    """Dil adını veya kodunu standart İngilizce dil adına çevir."""
    if not lang_input:
        return "English"
    key = lang_input.lower().strip()
    if key in LANGUAGE_MAP:
        return LANGUAGE_MAP[key]
    return lang_input.strip().title()


def translate_action(parameters: dict = None, player=None) -> str:
    params = parameters or {}
    action = params.get("action", "translate")
    text = params.get("text", "")
    target_lang = params.get("target_language", "English")
    source_lang = params.get("source_language", "")

    if player:
        player.write_log(f"[Translate] {source_lang} → {target_lang}")

    if not text:
        return "Çevrilecek metni belirtin efendim."

    target = _resolve_language(target_lang)
    source = _resolve_language(source_lang) if source_lang else ""

    try:
        import google.generativeai as genai
        genai.configure(api_key=_get_api_key())
        model = genai.GenerativeModel("gemini-3.1-flash")

        if action == "translate":
            source_hint = f" from {source}" if source else ""
            prompt = (
                f"Translate the following text{source_hint} to {target}. "
                f"Return ONLY the translation, nothing else.\n\n"
                f"Text: {text}"
            )
            response = model.generate_content(prompt)
            translated = response.text.strip()
            return f"🌐 [{target}]: {translated}"

        elif action == "detect":
            prompt = (
                f"What language is this text written in? "
                f"Reply with ONLY the language name in English.\n\n"
                f"Text: {text[:300]}"
            )
            response = model.generate_content(prompt)
            detected = response.text.strip()
            return f"Bu metin {detected} dilinde yazılmış efendim."

        elif action == "explain":
            prompt = (
                f"Explain the meaning of this word/phrase in {target}, "
                f"including usage examples and pronunciation guide:\n\n{text}"
            )
            response = model.generate_content(prompt)
            return response.text.strip()

        elif action == "multi":
            languages = params.get("languages", ["English", "German", "French"])
            if isinstance(languages, str):
                languages = [l.strip() for l in languages.split(",")]
            resolved = [_resolve_language(l) for l in languages]

            prompt = (
                f"Translate the following text to each of these languages: {', '.join(resolved)}. "
                f"Format: Language: translation\n\n"
                f"Text: {text}"
            )
            response = model.generate_content(prompt)
            return f"🌍 Çoklu Çeviri:\n{response.text.strip()}"

        return "Geçersiz çeviri komutu. Kullanılabilir: translate, detect, explain, multi"

    except Exception as e:
        return f"Çeviri hatası: {e}"
