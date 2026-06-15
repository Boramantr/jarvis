"""Merkezi yapılandırma — pydantic-settings.

Tüm sabitler ve ayarlanabilir parametreler tek yerde. Öncelik sırası:
  1. Ortam değişkeni (JARVIS_ önekli, örn. JARVIS_LIVE_MODEL)
  2. .env dosyası (proje kökünde)
  3. Buradaki varsayılanlar

API anahtarı geriye uyumluluk için hâlâ config/api_keys.json'dan da okunabilir.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_ROOT = Path(__file__).resolve().parent.parent


class JarvisConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="JARVIS_",
        env_file=str(_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Gemini / model ---
    gemini_api_key: str = ""
    live_model: str = "models/gemini-2.5-flash-native-audio-preview-12-2025"
    voice_name: str = "Charon"
    embedding_model: str = "text-embedding-004"
    reasoning_model: str = "gemini-2.5-flash"

    # --- Audio ---
    channels: int = 1
    send_sample_rate: int = 16000
    receive_sample_rate: int = 24000
    chunk_size: int = 1024
    audio_queue_max: int = 1000
    interrupt_rms: float = 0.18
    interrupt_streak: int = 5

    # --- Davranış ---
    safe_mode: bool = True
    ctx_cache_ttl: float = 60.0
    ctx_block_cap: int = 800
    ctx_total_cap: int = 6000

    # --- Uyandırma kelimesi ---
    wake_word_enabled: bool = True
    wake_word: str = "jarvis"

    # --- Konuşma algılama (VAD) — uzun cümlelerde araya girmesin ---
    vad_silence_ms: int = 1400         # bu kadar sessizlik olmadan turn bitmez
    vad_prefix_padding_ms: int = 300
    vad_end_sensitivity: str = "low"   # low = sonu geç algılar (uzun cümle dostu)

    # --- Servisler ---
    dashboard_enabled: bool = True
    dashboard_host: str = "127.0.0.1"
    dashboard_port: int = 8765

    # --- Reconnect ---
    reconnect_backoff_max: int = 30

    def resolve_api_key(self) -> str:
        """Öncelik: env → exe komşusu config → paketlenmiş config."""
        if self.gemini_api_key:
            return self.gemini_api_key
        candidates = []
        # Frozen ise exe komşu dizinini öne al (kullanıcı buraya kendi key'ini koyabilir)
        if getattr(sys, "frozen", False):
            candidates.append(Path(sys.executable).parent / "config" / "api_keys.json")
            meipass = getattr(sys, "_MEIPASS", None)
            if meipass:
                candidates.append(Path(meipass) / "config" / "api_keys.json")
        candidates.append(_ROOT / "config" / "api_keys.json")
        for path in candidates:
            if path.exists():
                try:
                    return json.loads(path.read_text(encoding="utf-8")).get("gemini_api_key", "")
                except Exception:
                    continue
        return ""


# Singleton — import edildiğinde bir kez yüklenir
settings = JarvisConfig()
