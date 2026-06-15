# PyInstaller spec — JARVIS (onedir)
#
# Build:   pyinstaller jarvis.spec --noconfirm --clean
# Output:  dist/JARVIS/JARVIS.exe  (+ _internal/)
#
# Neden onedir: actions/ klasörü çalışma anında AST ile taranır ve `architect`
# yeni araç dosyalarını diske yazar. onefile bunu engeller; onedir araçları
# _internal/actions altında gerçek .py olarak tutar.
import os
from pathlib import Path

from PyInstaller.utils.hooks import collect_all, collect_submodules

ROOT = Path(os.getcwd())

# --- Tüm action modüllerini hiddenimport yap → bağımlılıkları otomatik keşfedilir ---
action_modules = [
    f.stem for f in (ROOT / "actions").glob("*.py")
    if not f.name.startswith("__")
]

# --- Data dosyaları: kaynaklar _internal altına gider (get_base_dir = _MEIPASS) ---
datas = [
    ("actions", "actions"),          # AST tarama + architect yazımı + lazy import kaynağı
    ("config", "config"),            # api_keys.json (paketlenmiş kopya)
    ("core/prompt.txt", "core"),     # sistem prompt'u
    ("dashboard/reactor.html", "dashboard"),  # canlı arc reactor sayfası
]
if (ROOT / "face.png").exists():
    datas.append(("face.png", "."))

binaries = []
hiddenimports = list(action_modules) + [
    "dashboard.server",
    "core.config", "core.logging_setup", "core.live_state",
    "memory.vector_memory", "memory.transcripts", "memory.vault",
    "audioop",
]

# Data dosyası / dinamik import içeren paketler için tam toplama
for pkg in ("google.genai", "playwright", "pycaw", "comtypes",
            "pyttsx3", "gtts", "spotipy", "duckduckgo_search",
            "youtube_transcript_api", "uvicorn", "fastapi", "qrcode"):
    try:
        d, b, h = collect_all(pkg)
        datas += d; binaries += b; hiddenimports += h
    except Exception:
        pass

# PyQt6 alt modülleri
hiddenimports += collect_submodules("PyQt6")


a = Analysis(
    ["main.py"],
    pathex=["actions"],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "pytest", "ruff"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="JARVIS",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,             # pencere uygulaması (pythonw gibi)
    icon=str(ROOT / "assets" / "logo.ico") if (ROOT / "assets" / "logo.ico").exists() else (str(ROOT / "face.png") if (ROOT / "face.png").exists() else None),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="JARVIS",
)
