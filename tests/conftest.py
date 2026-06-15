"""Pytest fixtures — JARVIS test ortamı.

Gerçek ~/.jarvis dizinine dokunmamak için tüm dosya-tabanlı modüller
tmp_path'e yönlendirilir.
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "actions"))


@pytest.fixture
def tmp_jarvis_home(tmp_path, monkeypatch):
    """~/.jarvis yerine geçici dizin."""
    home = tmp_path / ".jarvis"
    home.mkdir()
    (home / "memory").mkdir()
    return home


@pytest.fixture
def isolated_episodic(tmp_jarvis_home, monkeypatch):
    """episodic modülünü geçici DB'ye yönlendir."""
    import memory.episodic as ep
    monkeypatch.setattr(ep, "DB_PATH", tmp_jarvis_home / "memory" / "episodic.db")
    monkeypatch.setattr(ep, "EPISODIC_DIR", tmp_jarvis_home / "memory" / "episodic")
    monkeypatch.setattr(ep, "_conn", None)
    yield ep
    if ep._conn is not None:
        ep._conn.close()
        ep._conn = None


@pytest.fixture
def isolated_memory(tmp_jarvis_home, monkeypatch):
    """memory_manager'ı geçici dosyaya yönlendir."""
    import memory.memory_manager as mm
    monkeypatch.setattr(mm, "MEMORY_PATH", tmp_jarvis_home / "memory" / "long_term.json")
    mm._cache["mtime"] = -1.0
    mm._cache["data"] = None
    yield mm
    mm._cache["mtime"] = -1.0
    mm._cache["data"] = None


@pytest.fixture
def isolated_vault(tmp_jarvis_home, monkeypatch):
    """vault'u geçici anahtara yönlendir."""
    import memory.vault as v
    monkeypatch.setattr(v, "_KEY_PATH", tmp_jarvis_home / ".key")
    monkeypatch.setattr(v, "_fernet", None)
    yield v
    v._fernet = None
