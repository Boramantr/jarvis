"""Vault (Fernet şifreleme) testleri."""


def test_roundtrip(isolated_vault):
    v = isolated_vault
    assert v.decrypt_text(v.encrypt_text("merhaba patron")) == "merhaba patron"


def test_unicode_payload(isolated_vault):
    v = isolated_vault
    text = "şğüöçıİ — 日本語 🚀"
    assert v.decrypt_text(v.encrypt_text(text)) == text


def test_is_encrypted_detection(isolated_vault):
    v = isolated_vault
    token = v.encrypt_text("data")
    assert v.is_encrypted(token)
    assert not v.is_encrypted('{"plain": "json"}')


def test_key_persistence(isolated_vault, tmp_jarvis_home):
    v = isolated_vault
    token = v.encrypt_text("x")
    # fernet reset — anahtar dosyadan yeniden yüklenmeli
    v._fernet = None
    assert v.decrypt_text(token) == "x"
    assert (tmp_jarvis_home / ".key").exists()


def test_wrong_key_raises(isolated_vault, tmp_jarvis_home):
    import pytest
    v = isolated_vault
    token = v.encrypt_text("secret")
    # anahtarı değiştir
    from cryptography.fernet import Fernet
    (tmp_jarvis_home / ".key").write_bytes(Fernet.generate_key())
    v._fernet = None
    with pytest.raises(ValueError):
        v.decrypt_text(token)
