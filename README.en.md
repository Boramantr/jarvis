<div align="center">

[🇹🇷 Türkçe](readme.md) · **🇬🇧 English**

<img src="assets/logo.png" alt="JARVIS" width="180" />

# JARVIS

### A Personal AI Assistant That Talks, Listens, and Remembers

A desktop AI assistant that lives on your computer, speaks with you in real time
through your microphone, opens and closes programs, manages your files, researches
on the web, and keeps personalized memories just for you.

`Windows` · `Python 3.12+` · `Gemini 3.1 Flash` · `PyQt6` · `SQLite` · `FastAPI`

</div>

---

## 🤔 What Is This? (Quick Summary)

JARVIS is a desktop program inspired by the **AI assistant from the Iron Man
movies**. Instead of typing at it, **you talk to it** — you say it into your
microphone, it answers out loud. The twist: it can actually **use your computer**.

> 🗣️ *"Play something chill on Spotify, summarize the report.pdf on my desktop,
> and save the summary as summary.docx."*
>
> JARVIS opens Spotify, reads the PDF, summarizes it, creates a Word document,
> and tells you out loud: "All done."

You don't have to script anything from scratch: it ships with **49+ built-in tools**.
If something is missing, it can **write a new tool for itself** and add it.

---

## 🚀 Easiest Install (Recommended)

No Python, no terminal. One click:

1. 👉 **[Download the latest release here](https://github.com/Boramantr/jarvis/releases/latest)**
2. Grab `JARVIS-Setup-1.0.0.exe` and run it
3. Follow the wizard (Next → Next → Install)
4. Launch JARVIS from the Start menu or desktop shortcut
5. On first launch it will ask for a **Gemini API key** →
   [get one free here](https://aistudio.google.com/apikey) (Google account is enough)

✅ **That's it.** Speak, and it will listen.

---

## ✨ What Can It Do?

| | |
|---|---|
| 🎙️ **Voice chat** | Talk instead of typing. You can interrupt — it doesn't freeze like a robot |
| 🛠️ **49+ built-in tools** | Spotify, YouTube, files, calendar, weather, translation, email, web search, coding... |
| 🧠 **Remembers you** | "Call me boss", "I'm vegetarian" — say it once, it remembers forever |
| 🤖 **Self-improves** | If a tool doesn't exist, *it writes one* and plugs it in |
| 💻 **Controls your PC** | Opens/closes apps, creates/moves/deletes files (asks first) |
| 🌐 **Browses the web** | Opens pages, fills forms, scrapes data, summarizes it |
| 🔒 **Safe** | Asks before destructive actions. Memory is encrypted |
| 📊 **Live dashboard** | `localhost:8765` → watch what it's doing in real time |

---

## 🎯 Example Commands

Say these in **natural English**, and JARVIS will do them:

| You say... | JARVIS does... |
|------------|----------------|
| *"Count the PDFs on my desktop"* | Writes Python with `code_runner`, runs it, reports back |
| *"Read the top 5 Hacker News headlines"* | Fetches the page, extracts headlines, reads them |
| *"Draft a summary and save it as report.docx"* | Generates a Word file |
| *"Summarize this PDF"* | Multimodal analysis via `analyze_file` |
| *"Remember to call me boss"* | Persists it with `update_memory` |
| *"What did we talk about last time?"* | Semantic recall via `vector_memory` |
| *"Check weather, add to calendar, send mail"* | 3-step plan via `plan_and_execute` |
| *"Write a tool that counts files"* | Spawns a permanent new capability via `architect` |
| *"Play focus music on Spotify"* | Opens Spotify, starts playing |
| *"What's my GPU temp?"* | Reads system sensors, tells you |

---

## 👨‍💻 Developer Setup (From Source)

For those who want to develop:

```bash
# 1. Clone the repo
git clone https://github.com/Boramantr/jarvis.git
cd jarvis

# 2. Dependencies
pip install -r requirements.txt

# 3. Browser engine (for browser_agent)
playwright install chromium

# 4. API key: create config/api_keys.json
# { "gemini_api_key": "AIza..." }

# 5. Run
python main.py
```

On first launch, the `~/.jarvis/` directory is created (memory, logs, encryption key).

### 📦 Build Your Own .exe

```bash
build_exe.bat   # or: pyinstaller jarvis.spec --noconfirm --clean
```

Output: `dist/JARVIS/JARVIS.exe` — you can move the whole `dist/JARVIS/` folder.

### 📥 Build Your Own Installer (Setup)

Requires [Inno Setup](https://jrsoftware.org/isdl.php):

```bash
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
```

Output: `installer_out/JARVIS-Setup-1.0.0.exe`

---

## ⚙️ Configuration

All settings live in [`core/config.py`](core/config.py). Override via `.env` or
`JARVIS_*` environment variables. See [`.env.example`](.env.example).

| Setting | Default | What it does |
|---------|---------|--------------|
| `JARVIS_SAFE_MODE` | `true` | Asks "are you sure?" on destructive actions |
| `JARVIS_VOICE_NAME` | `Charon` | TTS voice (`Charon`, `Aoede`, `Puck`...) |
| `JARVIS_INTERRUPT_RMS` | `0.18` | Barge-in threshold (higher = harder to interrupt) |
| `JARVIS_DASHBOARD_PORT` | `8765` | Web dashboard port |
| `JARVIS_CTX_TOTAL_CAP` | `6000` | Prompt context budget (chars) |
| `SENTRY_DSN` | — | Error tracking (optional) |

---

## 🏗️ How It Works

```
🎙️  Microphone ──► Gemini Live ──┬── 🔊 Speaker (talks back)
                                  └── 🛠️  Tool call ──► Result
```

Runs on a single `qasync` event loop (Qt UI + asyncio on the same thread).

| Layer | Contents |
|-------|----------|
| **main.py** | `JarvisLive` orchestrator — audio I/O, tool execution, context, reconnect |
| **actions/** | Each file is a tool (`<name>_action`), lazy import + AST discovery |
| **memory/** | vault (encryption), vector_memory (RAG), episodic (SQLite), transcripts |
| **core/** | config, logging, personality/emotion engines, prompt |
| **dashboard/** | FastAPI web dashboard |

Full architecture → [ARCHITECTURE.md](ARCHITECTURE.md)

---

## 🧪 Testing & Development

```bash
pip install -e ".[dev]"

pytest                                      # 37 tests
ruff check . --fix                          # lint + format
py-spy record -o profile.svg --pid <pid>    # live profiling
```

---

## 🔐 Data & Privacy

- 🏠 **Everything stays local** — data lives under `~/.jarvis/`, no cloud
- 🔐 **Encrypted memory** — persistent prefs encrypted with Fernet (AES-128)
- ⚠️ **Back up your key** — if `~/.jarvis/.key` is lost, encrypted memory can't be recovered
- 🛡️ **Code sandbox** — `code_runner` rejects destructive patterns (root deletion, disk format, fork-bombs)
- 📡 **Only Gemini sees voice/text** — no other service receives your data

---

## ❓ FAQ

**Does it work on Mac or Linux?**
From source (with Python), yes. The prebuilt installer is currently Windows-only.

**Is it paid?**
No. Gemini API's **generous free quota** is more than enough for personal use.

**Is my data sent to Google?**
Only the voice you speak in the moment is sent to Gemini. Persistent memory,
files, and history all stay on your machine.

**Does it work offline?**
No, a connection to Gemini is required. A fully offline alternative is on the roadmap.

**Can it recognize my voice?**
There's no speaker recognition yet — anyone nearby can talk to it.

---

## 📜 Origin & License

**Built by:** [Bora Mantar](https://github.com/Boramantr) — © 2026

Designed and developed from the ground up; the architecture, audio pipeline,
tool system, encrypted multi-layer memory, safety controls, web dashboard, and
observability layers were all hand-crafted into a customized release.
Change log → [CHANGELOG.md](CHANGELOG.md)

**License:** Free for personal and non-commercial use —
[CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/)

For commercial use, please reach out.

---

<div align="center">
<sub>⚡ Runs locally · No subscriptions · Full control is yours</sub>
<br><br>
⭐ If you like it, drop a star!
</div>
