"""Action discovery + tool declaration tutarlılık testleri."""
import ast
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ACTIONS = ROOT / "actions"


def _discover_actions() -> dict[str, str]:
    registry = {}
    for f in os.listdir(ACTIONS):
        if not f.endswith(".py") or f.startswith("__"):
            continue
        tree = ast.parse((ACTIONS / f).read_text(encoding="utf-8"))
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name.endswith("_action") and not node.name.startswith("_"):
                registry[node.name[: -len("_action")]] = f
    return registry


def test_all_action_files_parse():
    # _discover_actions zaten parse ediyor — SyntaxError fırlatırsa test düşer
    reg = _discover_actions()
    assert len(reg) >= 45


def test_declarations_match_implementations():
    import sys
    sys.path.insert(0, str(ROOT))
    from config.tool_declarations import TOOL_DECLARATIONS

    declared = {t["name"] for t in TOOL_DECLARATIONS}
    specials = {"system_power", "shutdown_jarvis", "profession_mode"}
    implemented = set(_discover_actions())

    missing_impl = (declared - specials) - implemented
    assert not missing_impl, f"Declared ama implementasyon yok: {missing_impl}"

    orphan = implemented - declared
    assert not orphan, f"Implementasyon var ama declared değil: {orphan}"


def test_declarations_have_required_fields():
    import sys
    sys.path.insert(0, str(ROOT))
    from config.tool_declarations import TOOL_DECLARATIONS

    for t in TOOL_DECLARATIONS:
        assert t.get("name"), "Tool 'name' eksik"
        assert t.get("description"), f"{t['name']}: description eksik"
        assert "parameters" in t, f"{t['name']}: parameters eksik"
