"""Conversation transcripts — tam konuşma metni kaydı.

Episodic 'summary' tutuyor; bu modül HAM metni saklar (debug + replay için).
Ayrı SQLite tablosu, WAL modu. Privacy: şifrelenmez ama dosya kullanıcı dizininde.
İstenirse export_day ile dışa aktarılır.
"""
from __future__ import annotations

import sqlite3
import threading
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = Path.home() / ".jarvis" / "memory" / "transcripts.db"
_lock = threading.Lock()
_conn: sqlite3.Connection | None = None


def _connect() -> sqlite3.Connection:
    global _conn
    if _conn is not None:
        return _conn
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    _conn = sqlite3.connect(str(DB_PATH), check_same_thread=False, isolation_level=None)
    _conn.execute("PRAGMA journal_mode=WAL")
    _conn.execute("PRAGMA synchronous=NORMAL")
    _conn.execute(
        """CREATE TABLE IF NOT EXISTS turns (
            id     INTEGER PRIMARY KEY AUTOINCREMENT,
            ts     TEXT NOT NULL,
            day    TEXT NOT NULL,
            role   TEXT NOT NULL,        -- user | assistant | tool
            text   TEXT NOT NULL,
            meta   TEXT
        )"""
    )
    _conn.execute("CREATE INDEX IF NOT EXISTS idx_turns_day ON turns(day)")
    _conn.execute("CREATE INDEX IF NOT EXISTS idx_turns_ts ON turns(ts)")
    return _conn


def log_turn(role: str, text: str, meta: str | None = None) -> None:
    if not text:
        return
    now = datetime.now()
    with _lock:
        _connect().execute(
            "INSERT INTO turns (ts, day, role, text, meta) VALUES (?,?,?,?,?)",
            (now.isoformat(timespec="seconds"), now.strftime("%Y-%m-%d"),
             role, text[:8000], meta),
        )


def get_recent_turns(n: int = 20) -> list[dict]:
    with _lock:
        rows = _connect().execute(
            "SELECT ts, role, text FROM turns ORDER BY id DESC LIMIT ?", (n,)
        ).fetchall()
    return [{"ts": r[0], "role": r[1], "text": r[2]} for r in reversed(rows)]


def export_day(date_str: str | None = None) -> str:
    """Bir günün konuşmasını düz metin olarak döndür."""
    date_str = date_str or datetime.now().strftime("%Y-%m-%d")
    with _lock:
        rows = _connect().execute(
            "SELECT ts, role, text FROM turns WHERE day=? ORDER BY id", (date_str,)
        ).fetchall()
    if not rows:
        return f"{date_str}: konuşma kaydı yok."
    lines = [f"=== Transcript {date_str} ==="]
    for ts, role, text in rows:
        hms = ts.split("T")[1] if "T" in ts else ts
        lines.append(f"[{hms}] {role.upper()}: {text}")
    return "\n".join(lines)


def cleanup_old(keep_days: int = 90) -> int:
    cutoff = (datetime.now() - timedelta(days=keep_days)).strftime("%Y-%m-%d")
    with _lock:
        cur = _connect().execute("DELETE FROM turns WHERE day < ?", (cutoff,))
        return cur.rowcount or 0
