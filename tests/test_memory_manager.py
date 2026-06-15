"""Long-term memory (şifreli) testleri."""


def test_empty_memory_structure(isolated_memory, isolated_vault):
    mm = isolated_memory
    m = mm.load_memory()
    assert set(m.keys()) >= {"identity", "preferences", "projects"}


def test_save_load_encrypted(isolated_memory, isolated_vault):
    mm = isolated_memory
    m = mm.load_memory()
    m["identity"]["address_as"] = {"value": "patron", "updated": "2026-06-07"}
    mm.save_memory(m)
    # Dosya şifreli mi?
    raw = mm.MEMORY_PATH.read_text(encoding="utf-8")
    assert raw.startswith("gAAAAA")
    # Cache reset edip yeniden oku
    mm._cache["mtime"] = -1.0
    mm._cache["data"] = None
    m2 = mm.load_memory()
    assert m2["identity"]["address_as"]["value"] == "patron"


def test_update_memory(isolated_memory, isolated_vault):
    mm = isolated_memory
    mm.update_memory({"preferences": {"coffee": {"value": "americano"}}})
    m = mm.load_memory()
    assert m["preferences"]["coffee"]["value"] == "americano"


def test_format_for_prompt_contains_identity(isolated_memory, isolated_vault):
    mm = isolated_memory
    mm.update_memory({"identity": {"name": {"value": "Bora"}}})
    out = mm.format_memory_for_prompt(mm.load_memory())
    assert "Bora" in out
