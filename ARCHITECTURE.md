# JARVIS — Architecture

This document describes the system's internal structure, data flow, and layers.

## High-level flow

```
Microphone ──► sounddevice ──► out_queue ──► Gemini Live (WebSocket)
                                                  │
              ┌───────────────────────────────────┤
              │                                   │
         AUDIO chunks                        function_call
              │                                   │
        audio_in_queue                      _execute_tool
              │                                   │
        sounddevice ◄── _play_audio        action_registry → tool
              │                                   │
          Speaker                          FunctionResponse ──► Gemini
```

Runs on a single `qasync` event loop (Qt UI + asyncio on the same thread). In the
old design asyncio lived on a separate daemon thread; the bridges were removed.

## Core components

### main.py — `JarvisLive`
The orchestrator. Responsibilities:
- **Audio I/O** — `_listen_audio` (mic→Gemini, barge-in detection), `_play_audio` (Gemini→speaker), backpressured `audio_in_queue`
- **Tool execution** — `_execute_tool`: confirmation gate → lazy resolve → executor → structured result + latency telemetry
- **Context** — `_gather_context`: merges 14 engine blocks under a token budget (800/block, 6000 total), with a 60s cache + background prefetch
- **Reconnect** — exponential backoff + circuit breaker (5 consecutive failures = long pause)
- **Graceful shutdown** — stops engines, closes DB/browser

### actions/ — Tool layer
Each `.py` file holds one or more `<name>_action(parameters, player)` functions.
- **Discovery**: scanned via AST at startup (not imported) → `action_registry: {tool: (module, fn)}`
- **Lazy import**: a tool's module loads on first call, then the result is cached → ~150–200 MB startup RAM savings
- **Prewarm**: the 5 most-used tools load in the background 3s after startup

Special tools (orchestration):
- `code_runner` — generic code execution (AST-sandboxed)
- `architect` — writes a new tool and adds it to the registry (hot-reload)
- `plan_and_execute` — produces a JSON plan in a separate Gemini turn + executes steps
- `vector_memory`, `update_memory`, `analyze_file`, `browser_agent`, `web_fetch`, `file_write`

### memory/ — Memory layers
| Module | Store | Purpose |
|--------|-------|---------|
| `vault.py` | `~/.jarvis/.key` | Fernet AES-128 encryption |
| `memory_manager.py` | `long_term.json` (encrypted) | Persistent prefs/identity — injected into every prompt |
| `vector_memory.py` | `vectors.db` | Gemini embeddings + cosine → semantic recall |
| `episodic.py` | `episodic.db` | Event/command history + tool telemetry + schema migrations |
| `transcripts.py` | `transcripts.db` | Raw conversation text (debug/replay) |
| `_jsoncache.py` | — | mtime-based JSON cache (routines/bond/social/goals) |

### core/ — Core
- `config.py` — pydantic-settings, all settings in one place (`.env` override)
- `logging_setup.py` — RotatingFileHandler + console + optional Sentry
- `personality*.py`, `emotion_engine.py`, `circadian.py` — personality/emotion context producers
- `prompt.txt` — system prompt (resourcefulness, addressing, confirmation rules)

### dashboard/ — Web dashboard
FastAPI, `localhost:8765`. Endpoints: `/api/stats`, `/api/telemetry`,
`/api/log`, `/api/transcript`, `/api/tools`, `/api/health`, `/api/memory`.

## Key design decisions

1. **SQLite > ChromaDB** — for vector search. numpy cosine is fast enough up to ~10K records, no extra service. See [docs/decisions/0001](docs/decisions/0001-sqlite-vs-chromadb.md).
2. **Lazy import** — 49 tools + heavy deps (cv2, playwright, pycaw) are not loaded at startup.
3. **qasync** — single event loop, no thread bridges.
4. **Confirmation gate** — destructive tools return `needs_confirmation` to the model, the model asks the user, then re-calls with `confirm=true`.
5. **Schema migrations** — `episodic._MIGRATIONS` + `PRAGMA user_version`, no alembic.

## Security model

- Long-term memory is encrypted (Fernet)
- `code_runner` AST checks: root deletion, fork-bombs, disk format are rejected
- `architect` forbids `eval/exec/__import__` in generated code
- `safe_mode` (on by default): 11 destructive tools require confirmation
- API key lives in `.env` or `config/api_keys.json`, must not be committed
