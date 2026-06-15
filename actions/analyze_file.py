"""analyze_file — Multimodal dosya analizi (Gemini).

Bir dosyayı (resim / PDF / ses / video / metin) Gemini'ye gönderir ve istenen
analizi yapar: özetle, sorulara cevap ver, OCR, içerik tanıma vb.

JARVIS Live oturumu sesli, bu yüzden büyük dosya analizi için ayrı bir
text-only çağrı yaparız.
"""
from __future__ import annotations

import json
import mimetypes
from pathlib import Path

from google import genai
from google.genai import types as gtypes

_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "api_keys.json"
_DEFAULT_MODEL = "gemini-3.1-flash"
_MAX_BYTES = 50_000_000  # 50 MB güvenlik tavanı

_client: genai.Client | None = None


def _get_client() -> genai.Client:
    global _client
    if _client is not None:
        return _client
    key = json.loads(_CONFIG_PATH.read_text(encoding="utf-8"))["gemini_api_key"]
    _client = genai.Client(api_key=key)
    return _client


def _guess_mime(path: Path) -> str:
    mime, _ = mimetypes.guess_type(str(path))
    if mime:
        return mime
    ext = path.suffix.lower()
    return {
        ".pdf": "application/pdf",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".gif": "image/gif",
        ".mp3": "audio/mpeg",
        ".wav": "audio/wav",
        ".m4a": "audio/mp4",
        ".mp4": "video/mp4",
        ".webm": "video/webm",
        ".txt": "text/plain",
        ".md": "text/markdown",
        ".csv": "text/csv",
        ".json": "application/json",
    }.get(ext, "application/octet-stream")


def analyze_file_action(parameters: dict | None = None, player=None) -> str:
    params = parameters or {}
    raw = (params.get("path") or "").strip()
    question = (params.get("question") or "Bu dosyayı özetle ve önemli noktaları çıkar.").strip()
    model = (params.get("model") or _DEFAULT_MODEL).strip()

    if not raw:
        return "Hata: path parametresi gerekli."

    path = Path(raw).expanduser()
    if not path.is_absolute():
        candidates = [Path.cwd() / raw, Path.home() / "Desktop" / raw, Path.home() / raw]
        path = next((c for c in candidates if c.exists()), candidates[0])

    if not path.exists():
        return f"Hata: dosya bulunamadı: {path}"
    if not path.is_file():
        return f"Hata: '{path}' bir dosya değil."

    size = path.stat().st_size
    if size > _MAX_BYTES:
        return f"Hata: dosya çok büyük ({size/1e6:.1f} MB > 50 MB)."

    mime = _guess_mime(path)
    if player:
        try:
            player.write_log(f"[analyze_file] {path.name} ({mime}, {size} B)")
        except Exception:
            pass

    try:
        client = _get_client()
        # Küçük dosyalar inline; büyükler için Files API daha doğru ama inline 20MB'a kadar OK
        if size <= 20_000_000:
            data = path.read_bytes()
            part = gtypes.Part.from_bytes(data=data, mime_type=mime)
            response = client.models.generate_content(
                model=model,
                contents=[part, question],
            )
        else:
            uploaded = client.files.upload(file=str(path))
            response = client.models.generate_content(
                model=model,
                contents=[uploaded, question],
            )

        text = (getattr(response, "text", None) or "").strip()
        return text or "(Gemini boş yanıt döndü)"
    except Exception as e:
        return f"Hata: analiz başarısız ({type(e).__name__}: {e})."
