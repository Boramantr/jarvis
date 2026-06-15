"""update_memory — Kullanıcının kalıcı tercihlerini ve kimliğini long_term.json'a yazar.

vector_memory'den farkı: bunlar her turda prompt'a otomatik enjekte edilir
(format_memory_for_prompt zinciri). Hitap tarzı, isim, dil tercihi, sevdiği
şeyler vb. burada saklanmalı.

Kategoriler:
  identity      → name, age, address_as (hitap), job, language, ...
  preferences   → kahve_tercihi, müzik_türü, çalışma_saati, ...
  projects      → aktif projeler / hedefler
  relationships → ailesi, ekibi
  wishes        → istekleri
  notes         → kısa notlar
"""
from __future__ import annotations

from memory.memory_manager import load_memory, update_memory

_VALID_CATEGORIES = {"identity", "preferences", "projects", "relationships", "wishes", "notes"}


def update_memory_action(parameters: dict | None = None, player=None) -> str:
    params = parameters or {}
    action = (params.get("action") or "set").strip().lower()

    if action == "list":
        memory = load_memory()
        cat = params.get("category")
        if cat:
            data = memory.get(cat, {})
            if not data:
                return f"{cat}: boş."
            lines = [f"{cat}:"]
            for k, v in data.items():
                val = v.get("value") if isinstance(v, dict) else v
                lines.append(f"  {k}: {val}")
            return "\n".join(lines)
        # Tüm kategoriler
        lines = []
        for c in _VALID_CATEGORIES:
            n = len(memory.get(c, {}))
            if n:
                lines.append(f"{c}: {n} kayıt")
        return "\n".join(lines) or "Bellek boş."

    if action == "delete":
        category = (params.get("category") or "").strip().lower()
        key = (params.get("key") or "").strip().lower()
        if not category or not key:
            return "Hata: delete için category ve key gerekli."
        memory = load_memory()
        if category in memory and key in memory[category]:
            del memory[category][key]
            from memory.memory_manager import save_memory
            save_memory(memory)
            return f"Silindi: {category}/{key}"
        return f"Bulunamadı: {category}/{key}"

    # action == "set" (varsayılan)
    category = (params.get("category") or "preferences").strip().lower()
    key = (params.get("key") or "").strip().lower().replace(" ", "_")
    value = params.get("value")

    if category not in _VALID_CATEGORIES:
        return f"Hata: kategori '{category}' geçersiz. Kullan: {sorted(_VALID_CATEGORIES)}"
    if not key:
        return "Hata: key gerekli (örn. 'address_as', 'favorite_food')."
    if not value:
        return "Hata: value gerekli."

    update_memory({category: {key: {"value": str(value)[:380]}}})
    return f"✅ Kaydedildi: {category}/{key} = {str(value)[:60]}"
