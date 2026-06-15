"""Config (pydantic-settings) testleri."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def test_defaults():
    from core.config import JarvisConfig
    c = JarvisConfig(_env_file=None)
    assert c.live_model.startswith("models/")
    assert c.safe_mode is True
    assert c.dashboard_port == 8765
    assert c.interrupt_rms == 0.18


def test_env_override(monkeypatch):
    monkeypatch.setenv("JARVIS_DASHBOARD_PORT", "9999")
    monkeypatch.setenv("JARVIS_SAFE_MODE", "false")
    from core.config import JarvisConfig
    c = JarvisConfig(_env_file=None)
    assert c.dashboard_port == 9999
    assert c.safe_mode is False


def test_resolve_api_key_from_env(monkeypatch):
    monkeypatch.setenv("JARVIS_GEMINI_API_KEY", "test-key-123")
    from core.config import JarvisConfig
    c = JarvisConfig(_env_file=None)
    assert c.resolve_api_key() == "test-key-123"
