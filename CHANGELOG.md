# Changelog

[Keep a Changelog](https://keepachangelog.com/) format, [SemVer](https://semver.org/).

## [0.4.0] — 2026-06-11

Production-grade infrastructure, new capabilities, and extensive optimization.

### Added
- **Test infrastructure** — pytest (37 tests), ruff lint, `pyproject.toml` packaging
- **Structured logging** — RotatingFileHandler + unicode-safe console + optional Sentry
- **Centralized config** — `core/config.py` (pydantic-settings), `.env` support
- **Telemetry** — per-tool latency/success, dashboard panel, SQLite schema migrations
- **Graceful shutdown** — engine stopping, DB/browser closing; circuit breaker (5 failures = pause)
- **Conversation transcripts** — raw text in SQLite, dashboard `/api/transcript`
- **Encrypted memory** — Fernet AES-128, `~/.jarvis/.key`
- **Confirmation layer** — confirmation on destructive tools (safe_mode)
- **Semantic memory (RAG)** — Gemini embeddings + SQLite + cosine; automatic conversation capture
- **Architect** — writes its own tool and hot-reloads it (AST security-checked)
- **ReAct planner** — `plan_and_execute` multi-step task orchestration
- **Voice interrupt** — barge-in during TTS
- **Web dashboard** — FastAPI `localhost:8765`
- **New tools** — `code_runner`, `web_fetch`, `file_write`, `analyze_file`, `browser_agent`, `vector_memory`, `update_memory`, `architect`, `plan_and_execute`
- **code_runner sandbox** — AST + shell pattern checks (root deletion, fork-bomb, format rejection)

### Changed
- **Event loop** — qasync unifies Qt+asyncio on a single thread (thread bridges removed)
- **Episodic** — JSON-per-day → SQLite (O(log N) queries, automatic migration)
- **Audio** — audioop-lts native RMS, backpressured queue (no drops)
- **psutil** — non-blocking cpu_percent
- **Prompt** — resourcefulness protocol ("never say I can't"), addressing rule (`address_as`)
- **main.py** — 1061 → ~700 lines; TOOL_DECLARATIONS moved to a separate file

### Performance
- Lazy import: ~150–200 MB startup RAM savings (49 tools + heavy deps)
- Context cache (60s) + background prefetch
- Browser idle timeout (5min → Chromium closes, ~300–500 MB reclaimed)
- Relaxed polling intervals
- `requests.Session` keepalive, tool prewarm

### Fixed
- Reconnect thread/counter leak (start guard)
- Silent `except: pass` → logging
- Windows cp1252 emoji print crashes
- Memory mtime cache (avoids redundant JSON re-parsing)

### Removed
- Dead `agent/` modules (planner, executor, error_handler, task_queue)
- Duplicate `smart_researcher.py`
- 9 dead tool declarations

---

## [0.3.0] and earlier
Original MARK XXXIX (FatihMakes) base — voice dialogue, system control, personality
and memory engines. See [readme.md](readme.md).
