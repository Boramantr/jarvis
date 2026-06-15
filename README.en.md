<div align="center">

[🇹🇷 Türkçe](readme.md) · **🇬🇧 English**

# 🤖 JARVIS

### Voice-Driven, Tool-Using, Memory-Backed Personal AI Assistant

A desktop AI assistant built on Gemini Live (native audio).
It speaks, listens, controls your computer with **49+ tools**, remembers your past,
and **writes its own new capabilities** when needed.

`Python 3.12+` · `Gemini 2.5 Flash` · `PyQt6` · `SQLite` · `FastAPI`

</div>

---

## ✨ What Can It Do?

| | |
|---|---|
| 🎙️ **Real-time voice dialogue** | Native audio, fluent conversation — **you can interrupt it** (barge-in) |
| 🛠️ **49+ tools** | Spotify, YouTube, system control, files, calendar, weather, translation, cybersecurity, accounting, architecture calcs... |
| 🧠 **Multi-layer memory** | Encrypted persistent prefs + semantic (vector) recall + episodic history + conversation transcripts |
| 🤖 **Self-improvement** | Writes new tools via `architect`; plans and executes multi-step tasks via `plan_and_execute` |
| 💻 **Generic code execution** | When no tool fits, it writes and runs Python/PowerShell — never says "I can't" |
| 🌐 **Browser control** | Navigate pages, fill forms, scrape data with Playwright |
| 🔒 **Security** | Confirmation on destructive actions, encrypted memory, code sandbox |
| 📊 **Web dashboard** | `localhost:8765` — live stats, telemetry, logs, transcripts |

---

## 🚀 Installation

```bash
# 1. Dependencies
pip install -r requirements.txt

# 2. Browser engine (for browser_agent)
playwright install chromium
```

### API Key

Either method works:

```jsonc
// config/api_keys.json
{ "gemini_api_key": "AIza..." }
```

```bash
# or .env (copy .env.example)
JARVIS_GEMINI_API_KEY=AIza...
```

> [Get a free Gemini API key →](https://aistudio.google.com/apikey)

### Run

```bash
python main.py        # or JARVIS.bat (Windows)
```

On first launch, the `~/.jarvis/` directory is created (memory, logs, encryption key).

---

## 🎯 Example Commands

| If you say... | JARVIS... |
|---------------|-----------|
| *"Count the PDFs on my desktop"* | writes Python with `code_runner` and runs it |
| *"Read the top 5 Hacker News headlines"* | fetches the page with `web_fetch` |
| *"Draft a summary and save it as report.docx"* | generates a Word file with `file_write` |
| *"Summarize this PDF"* | runs multimodal analysis with `analyze_file` |
| *"Remember to call me boss"* | persists it with `update_memory` |
| *"What did we talk about last time?"* | semantically recalls with `vector_memory` |
| *"Check weather, add to calendar, send mail"* | builds a multi-step plan with `plan_and_execute` |
| *"Write a tool that counts files"* | spawns a permanent new capability via `architect` |

---

## ⚙️ Configuration

All settings live in [`core/config.py`](core/config.py); override via `.env` or
`JARVIS_*` environment variables. See [`.env.example`](.env.example).

| Setting | Default | Description |
|---------|---------|-------------|
| `JARVIS_SAFE_MODE` | `true` | Require confirmation on destructive tools |
| `JARVIS_VOICE_NAME` | `Charon` | TTS voice |
| `JARVIS_INTERRUPT_RMS` | `0.18` | Barge-in threshold (raise = harder to interrupt) |
| `JARVIS_DASHBOARD_PORT` | `8765` | Web dashboard port |
| `JARVIS_CTX_TOTAL_CAP` | `6000` | Prompt context budget (characters) |
| `SENTRY_DSN` | — | Error tracking (optional) |

---

## 🏗️ Architecture

```
Microphone → Gemini Live → ┬─ AUDIO → speaker (barge-in capable)
                            └─ tool_call → action_registry → tool → result
```

Runs on a single `qasync` event loop (Qt UI + asyncio on the same thread).

| Layer | Contents |
|-------|----------|
| **main.py** | `JarvisLive` orchestrator — audio I/O, tool execution, context, reconnect |
| **actions/** | Each file is a tool (`<name>_action`), lazy import + AST discovery |
| **memory/** | vault (encryption), vector_memory (RAG), episodic (SQLite), transcripts |
| **core/** | config, logging, personality/emotion engines, prompt |
| **dashboard/** | FastAPI web dashboard |

Details → [ARCHITECTURE.md](ARCHITECTURE.md)

---

## 🧪 Development

```bash
pip install -e ".[dev]"

pytest                                      # 37 tests
ruff check . --fix                          # lint + format
py-spy record -o profile.svg --pid <pid>    # live profiling
```

---

## 🔐 Data & Privacy

- **Everything is local** — data lives under `~/.jarvis/`, no cloud.
- **Encrypted memory** — persistent preferences encrypted with Fernet (AES-128).
- ⚠️ **Back up your key** — if `~/.jarvis/.key` is lost, encrypted memory can't be recovered.
- **Code sandbox** — `code_runner` rejects destructive patterns like root deletion, disk format, fork-bombs.

---

## 📜 Origin & License

Built on top of the [FatihMakes / MARK XXXIX](https://www.youtube.com/@FatihMakes)
base, as a customized version with added architecture, performance, security, and
observability layers. Changes → [CHANGELOG.md](CHANGELOG.md)

Personal, non-commercial use — [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/)

---

<div align="center">
<sub>⚡ Runs locally · No subscriptions · Full control is yours</sub>
</div>
