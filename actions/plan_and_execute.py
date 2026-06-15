"""plan_and_execute — Çoklu adım hedef için ReAct tarzı plan+yürüt.

Gemini sync text-modelini ayrı bir oturumda kullanır (Live oturumu sesli ve hızlı,
planlama için ayrı bir 'reasoning' turu mantıklı). Önce JSON adım listesi üretir,
sonra her adımı gerçek action_registry üzerinden çalıştırır.

Model çağırma sözleşmesi:
    parameters = {"goal": "...", "max_steps": 5}
    -> "Plan: ...\\nAdım 1: ... → sonuç ...\\n..."

Notlar:
- Adım sırası SIRAYLA çalışır (sonuç bir sonrakini etkileyebilir).
- Her adımın çıktısı 400 char'a kırpılır — döngü prompt'unu şişirmesin.
- Hata bir adımı durdurmaz; bir sonraki devam eder. Sonunda özet döner.
"""
from __future__ import annotations

import importlib
import json
from pathlib import Path

_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "api_keys.json"
_MODEL = "gemini-3.1-flash"
_MAX_STEPS = 8
_client = None


def _get_client():
    global _client
    if _client is not None:
        return _client
    from google import genai
    key = json.loads(_CONFIG_PATH.read_text(encoding="utf-8"))["gemini_api_key"]
    _client = genai.Client(api_key=key)
    return _client


def _list_available_tools() -> list[str]:
    """actions/ klasöründen mevcut tool isimlerini AST ile (import etmeden) çıkar."""
    import ast as _ast
    actions_dir = Path(__file__).resolve().parent
    tools = []
    for f in actions_dir.glob("*.py"):
        if f.name.startswith("_") or f.name == "plan_and_execute.py":
            continue
        try:
            tree = _ast.parse(f.read_text(encoding="utf-8"))
            for node in tree.body:
                if isinstance(node, _ast.FunctionDef) and node.name.endswith("_action") and not node.name.startswith("_"):
                    tools.append(node.name[:-len("_action")])
        except Exception:
            continue
    return sorted(tools)


_PLAN_PROMPT = """Aşağıdaki hedefe ulaşmak için bir eylem planı çıkar.

HEDEF:
{goal}

KULLANILABİLİR TOOL'LAR (sadece bunlar):
{tools}

KURALLAR:
- En fazla {max_steps} adım.
- Sıralı ve mantıklı ol; her adım bir öncekinin sonucundan yararlanabilir.
- Çıktı SADECE JSON dizi olsun. Açıklama ekleme.
- Her adım: {{"step": <num>, "tool": "<isim>", "args": {{...}}, "why": "<kısa neden>"}}
- "args" doğrudan tool'a verilecek parametre dict'i.
- Eğer hedef tek tool'la zaten karşılanabilirse 1 adımlık plan dön."""


def _plan(goal: str, max_steps: int, tools: list[str]) -> list[dict]:
    client = _get_client()
    prompt = _PLAN_PROMPT.format(
        goal=goal,
        tools=", ".join(tools),
        max_steps=max_steps,
    )
    resp = client.models.generate_content(model=_MODEL, contents=prompt)
    text = (getattr(resp, "text", None) or "").strip()
    # JSON parse — bazen ```json ... ``` fence'leriyle gelir
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```", 2)[1] if text.count("```") >= 2 else text
        if text.startswith("json"):
            text = text[4:]
        text = text.strip("` \n")
    try:
        plan = json.loads(text)
        if isinstance(plan, list):
            return plan[:max_steps]
    except Exception:
        pass
    # Düz metin döndüyse boş plan
    return []


def _exec_step(tool: str, args: dict) -> str:
    """Verilen tool'u import edip çalıştır. Hata mesajı string olarak döner."""
    try:
        mod = importlib.import_module(tool)
        fn = getattr(mod, f"{tool}_action", None)
        if fn is None:
            return f"[skip] {tool} bulunamadı."
        result = fn(parameters=args, player=None)
        return str(result)[:400]
    except Exception as e:
        return f"[error] {type(e).__name__}: {e}"


def plan_and_execute_action(parameters: dict | None = None, player=None) -> str:
    params = parameters or {}
    goal = (params.get("goal") or "").strip()
    if not goal:
        return "Hata: goal parametresi gerekli."
    try:
        max_steps = min(int(params.get("max_steps") or 5), _MAX_STEPS)
    except Exception:
        max_steps = 5

    if player:
        try: player.write_log(f"[plan] hedef: {goal[:80]}")
        except Exception: pass

    tools = _list_available_tools()
    try:
        plan = _plan(goal, max_steps, tools)
    except Exception as e:
        return f"Plan üretilemedi: {type(e).__name__}: {e}"

    if not plan:
        return ("Hata: model geçerli bir JSON plan üretmedi. Goal'i daha somut yazıp "
                "tek bir tool çağrısı yap.")

    lines = [f"📋 Plan ({len(plan)} adım): {goal[:80]}"]
    for step in plan:
        n = step.get("step", "?")
        tool = step.get("tool", "")
        args = step.get("args", {}) or {}
        why = step.get("why", "")
        if not tool:
            lines.append(f"  [{n}] (boş tool atlandı)")
            continue
        if player:
            try: player.write_log(f"[plan {n}/{len(plan)}] {tool}")
            except Exception: pass
        out = _exec_step(tool, args)
        lines.append(f"  [{n}] {tool}({json.dumps(args, ensure_ascii=False)[:80]})")
        if why:
            lines.append(f"      → niye: {why[:120]}")
        lines.append(f"      → sonuç: {out[:300]}")
    return "\n".join(lines)
