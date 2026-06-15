import platform
import shutil
import subprocess
import time

try:
    import psutil
    _PSUTIL = True
except ImportError:
    _PSUTIL = False

_SYSTEM = platform.system()

_APP_ALIASES: dict[str, dict[str, str]] = {
    "chrome":             {"Windows": "chrome",            "Darwin": "Google Chrome",        "Linux": "google-chrome"},
    "google chrome":      {"Windows": "chrome",            "Darwin": "Google Chrome",        "Linux": "google-chrome"},
    "firefox":            {"Windows": "firefox",           "Darwin": "Firefox",              "Linux": "firefox"},
    "edge":               {"Windows": "msedge",            "Darwin": "Microsoft Edge",       "Linux": "microsoft-edge"},
    "brave":              {"Windows": "brave",             "Darwin": "Brave Browser",        "Linux": "brave-browser"},
    "whatsapp":           {"Windows": "WhatsApp",          "Darwin": "WhatsApp",             "Linux": "whatsapp"},
    "telegram":           {"Windows": "Telegram",          "Darwin": "Telegram",             "Linux": "telegram"},
    "discord":            {"Windows": "Discord",           "Darwin": "Discord",              "Linux": "discord"},
    "slack":              {"Windows": "Slack",             "Darwin": "Slack",                "Linux": "slack"},
    "zoom":               {"Windows": "Zoom",              "Darwin": "zoom.us",              "Linux": "zoom"},
    "spotify":            {"Windows": "Spotify",           "Darwin": "Spotify",              "Linux": "spotify"},
    "vlc":                {"Windows": "vlc",               "Darwin": "VLC",                  "Linux": "vlc"},
    "vscode":             {"Windows": "code",              "Darwin": "Visual Studio Code",   "Linux": "code"},
    "visual studio code": {"Windows": "code",              "Darwin": "Visual Studio Code",   "Linux": "code"},
    "vs code":            {"Windows": "code",              "Darwin": "Visual Studio Code",   "Linux": "code"},
    "terminal":           {"Windows": "wt",                "Darwin": "Terminal",             "Linux": "gnome-terminal"},
    "cmd":                {"Windows": "cmd.exe",           "Darwin": "Terminal",             "Linux": "gnome-terminal"},
    "powershell":         {"Windows": "powershell.exe",    "Darwin": "Terminal",             "Linux": "gnome-terminal"},
    "notepad":            {"Windows": "notepad.exe",       "Darwin": "TextEdit",             "Linux": "gedit"},
    "notepad++":          {"Windows": "notepad++",         "Darwin": "TextEdit",             "Linux": "gedit"},
    "explorer":           {"Windows": "explorer.exe",      "Darwin": "Finder",               "Linux": "nautilus"},
    "file explorer":      {"Windows": "explorer.exe",      "Darwin": "Finder",               "Linux": "nautilus"},
    "task manager":       {"Windows": "taskmgr.exe",       "Darwin": "Activity Monitor",     "Linux": "gnome-system-monitor"},
    "calculator":         {"Windows": "calc.exe",          "Darwin": "Calculator",           "Linux": "gnome-calculator"},
    "word":               {"Windows": "winword",           "Darwin": "Microsoft Word",       "Linux": "libreoffice --writer"},
    "excel":              {"Windows": "excel",             "Darwin": "Microsoft Excel",      "Linux": "libreoffice --calc"},
    "powerpoint":         {"Windows": "powerpnt",          "Darwin": "Microsoft PowerPoint", "Linux": "libreoffice --impress"},
    "steam":              {"Windows": "steam",             "Darwin": "Steam",                "Linux": "steam"},
    "epic games":         {"Windows": "EpicGamesLauncher", "Darwin": "Epic Games Launcher",  "Linux": "legendary"},
    "notion":             {"Windows": "Notion",            "Darwin": "Notion",               "Linux": "notion"},
    "obsidian":           {"Windows": "Obsidian",          "Darwin": "Obsidian",             "Linux": "obsidian"},
    "obs":                {"Windows": "obs64",             "Darwin": "OBS",                  "Linux": "obs"},
    "obs studio":         {"Windows": "obs64",             "Darwin": "OBS",                  "Linux": "obs"},
    "figma":              {"Windows": "Figma",             "Darwin": "Figma",                "Linux": "figma"},
    "postman":            {"Windows": "Postman",           "Darwin": "Postman",              "Linux": "postman"},
    "unity":              {"Windows": "Unity Hub",         "Darwin": "Unity Hub",            "Linux": "unityhub"},
    "blender":            {"Windows": "blender",           "Darwin": "Blender",              "Linux": "blender"},
    "premiere":           {"Windows": "Adobe Premiere Pro","Darwin": "Adobe Premiere Pro",   "Linux": "premiere"},
    "photoshop":          {"Windows": "Photoshop",         "Darwin": "Adobe Photoshop",      "Linux": "photoshop"},
    "teams":              {"Windows": "Teams",             "Darwin": "Microsoft Teams",      "Linux": "teams"},
    "paint":              {"Windows": "mspaint.exe",       "Darwin": "Preview",              "Linux": "gimp"},
    "gimp":               {"Windows": "gimp",              "Darwin": "GIMP",                 "Linux": "gimp"},
    "audacity":           {"Windows": "Audacity",          "Darwin": "Audacity",             "Linux": "audacity"},
    "valorant":           {"Windows": "valorant",          "Darwin": "",                     "Linux": ""},
    "minecraft":          {"Windows": "Minecraft Launcher","Darwin": "Minecraft",            "Linux": "minecraft"},
    "cursor":             {"Windows": "Cursor",            "Darwin": "Cursor",               "Linux": "cursor"},
    "settings":           {"Windows": "ms-settings:",      "Darwin": "System Preferences",   "Linux": "gnome-control-center"},
}

def _normalize(raw: str) -> str:
    key = raw.lower().strip()
    if key in _APP_ALIASES:
        return _APP_ALIASES[key].get(_SYSTEM, raw)
    for alias_key, os_map in _APP_ALIASES.items():
        if alias_key in key or key in alias_key:
            return os_map.get(_SYSTEM, raw)
    return raw

def _launch_windows(app_name: str) -> bool:
    if shutil.which(app_name) or shutil.which(app_name.split(".")[0]):
        try:
            subprocess.Popen(app_name, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(1.5)
            return True
        except Exception as e:
            print(f"[open_app] subprocess failed: {e}")
    if ":" in app_name:
        try:
            subprocess.Popen(f"start {app_name}", shell=True)
            time.sleep(1.0)
            return True
        except Exception:
            pass
    try:
        import pyautogui
        pyautogui.PAUSE = 0.1
        pyautogui.press("win")
        time.sleep(0.7)
        pyautogui.write(app_name, interval=0.05)
        time.sleep(0.9)
        pyautogui.press("enter")
        time.sleep(2.5)
        return True
    except Exception as e:
        print(f"[open_app] Start Menu search failed: {e}")
    return False

def open_app_action(
    parameters=None,
    response=None,
    player=None,
    session_memory=None,
) -> str:
    app_name = (parameters or {}).get("app_name", "").strip()
    if not app_name:
        return "No application name provided."

    normalized = _normalize(app_name)
    print(f"[open_app] Launching: '{app_name}' → '{normalized}' ({_SYSTEM})")
    if player:
        player.write_log(f"[open_app] {app_name}")

    try:
        if _SYSTEM == "Windows":
            if _launch_windows(normalized):
                return f"Opened {app_name}."
            if normalized.lower() != app_name.lower() and _launch_windows(app_name):
                return f"Opened {app_name}."
        return f"Could not confirm that {app_name} launched. It may still be loading, or it might not be installed."
    except Exception as e:
        return f"Failed to open {app_name}: {e}"
