"""vector_memory aksiyonu — semantik bellek yönetimi.

JARVIS bu tool ile geçmiş konuşmaları/notları semantik olarak arar veya
kalıcı bir bilgi ekler.

Yaygın kullanım:
- recall: "Geçen ay X projesi hakkında ne dedik?"
- remember: "Bu bilgiyi unutma: kahve makinemin markası Breville."
- stats / clear: yönetim
"""
from __future__ import annotations

from memory import vector_memory as vm


def vector_memory_action(parameters: dict | None = None, player=None) -> str:
    params = parameters or {}
    action = (params.get("action") or "").strip().lower()

    if action == "remember":
        text = params.get("text") or ""
        kind = params.get("kind") or "note"
        rid = vm.remember(text, kind=kind, meta=params.get("meta"))
        return f"Hatırlandı (id={rid})." if rid > 0 else "Boş içerik veya embedding hatası."

    if action == "recall":
        q = params.get("query") or ""
        try:
            k = int(params.get("k") or 5)
        except Exception:
            k = 5
        hits = vm.recall(q, k=k, kind=params.get("kind"))
        if not hits:
            return "İlgili bir kayıt bulamadım."
        lines = [f"En benzer {len(hits)} kayıt:"]
        for score, text, meta in hits:
            snippet = text.replace("\n", " ")[:200]
            lines.append(f"  ({score:.2f}) {snippet}")
        return "\n".join(lines)

    if action == "stats":
        s = vm.stats()
        return f"Toplam: {s['total']}, türler: {s['by_kind']}, embed cache: {s['embed_cache']}"

    if action == "clear":
        n = vm.clear(kind=params.get("kind"))
        return f"{n} kayıt silindi."

    return "Hata: action gerekli (remember | recall | stats | clear)."
