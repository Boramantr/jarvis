"""Vault — Fernet AES-128 simetrik şifreleme.

Anahtar `~/.jarvis/.key`'de saklanır (sadece kullanıcı okuyabilir).
İlk açılışta otomatik üretilir. Yedeğini güvenli yere kopyala — anahtar
kaybedilirse şifreli memory geri açılamaz.

Kullanım:
    from memory.vault import encrypt_text, decrypt_text, encrypt_bytes, decrypt_bytes
"""
from __future__ import annotations

import os
import stat
from pathlib import Path
from threading import Lock

from cryptography.fernet import Fernet, InvalidToken

_KEY_PATH = Path.home() / ".jarvis" / ".key"
_lock = Lock()
_fernet: Fernet | None = None


def _load_or_create_key() -> bytes:
    _KEY_PATH.parent.mkdir(parents=True, exist_ok=True)
    if _KEY_PATH.exists():
        return _KEY_PATH.read_bytes().strip()
    key = Fernet.generate_key()
    _KEY_PATH.write_bytes(key)
    try:
        # Windows'ta da no-op; *nix'te sadece owner read/write
        os.chmod(_KEY_PATH, stat.S_IRUSR | stat.S_IWUSR)
    except Exception:
        pass
    return key


def _get_fernet() -> Fernet:
    global _fernet
    with _lock:
        if _fernet is None:
            _fernet = Fernet(_load_or_create_key())
        return _fernet


def encrypt_bytes(data: bytes) -> bytes:
    return _get_fernet().encrypt(data)


def decrypt_bytes(token: bytes) -> bytes:
    try:
        return _get_fernet().decrypt(token)
    except InvalidToken:
        raise ValueError("Şifreli veri açılamadı — anahtar yanlış veya bozulmuş.")


def encrypt_text(text: str) -> str:
    return encrypt_bytes(text.encode("utf-8")).decode("ascii")


def decrypt_text(token: str) -> str:
    return decrypt_bytes(token.encode("ascii")).decode("utf-8")


def is_encrypted(text_or_bytes) -> bool:
    """Heuristic: Fernet token 'gAAAAA' ile başlar."""
    if isinstance(text_or_bytes, bytes):
        return text_or_bytes.startswith(b"gAAAAA")
    return isinstance(text_or_bytes, str) and text_or_bytes.startswith("gAAAAA")
