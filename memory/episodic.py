"""Episodic Memory — SQLite tabanlı olay/komut geçmişi.

Önceki sürüm günde bir JSON dosyası tutuyordu; her sorguda dosyalar açılıp
parse ediliyordu. Bu sürüm tek SQLite veritabanı kullanır:
  • O(log N) sorgular (zaman indeksli)
  • RAM üzerinde sabit footprint
  • Eski JSON dosyaları ilk açılışta otomatik migrate edilir

Public API geriye dönük: log_event, log_command, get_today_summary,
get_recent_context, get_day_history, get_available_days, cleanup_old,
get_tool_hints.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from threading import Lock

EPISODIC_DIR = Path.home() / ".jarvis" / "memory" / "episodic"
DB_PATH = Path.home() / ".jarvis" / "memory" / "episodic.db"
_lock = Lock()
_conn: sqlite3.Connection | None = None


def _ensure_dir():
    EPISODIC_DIR.mkdir(parents=True, exist_ok=True)
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def _connect() -> sqlite3.Connection:
    global _conn
    if _conn is not None:
        return _conn
    _ensure_dir()
    _conn = sqlite3.connect(str(DB_PATH), check_same_thread=False, isolation_level=None)
    _conn.execute("PRAGMA journal_mode=WAL")
    _conn.execute("PRAGMA synchronous=NORMAL")
    _conn.execute(
        """CREATE TABLE IF NOT EXISTS events (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            ts        TEXT NOT NULL,        -- ISO 8601, lex-sortable
            day       TEXT NOT NULL,        -- YYYY-MM-DD
            hms       TEXT NOT NULL,        -- HH:MM:SS
            category  TEXT NOT NULL,
            summary   TEXT NOT NULL,
            mood      TEXT,
            tool      TEXT,
            ok        INTEGER DEFAULT 1,
            meta_json TEXT
        )"""
    )
    _conn.execute("CREATE INDEX IF NOT EXISTS idx_events_day ON events(day)")
    _conn.execute("CREATE INDEX IF NOT EXISTS idx_events_ts ON events(ts)")
    _conn.execute("CREATE INDEX IF NOT EXISTS idx_events_cat ON events(category)")
    _conn.execute("CREATE INDEX IF NOT EXISTS idx_events_tool ON events(tool)")
    _run_migrations(_conn)
    _migrate_json_if_needed()
    return _conn


# ── Schema migrations ──
# Her giriş: (versiyon, açıklama, SQL). user_version PRAGMA ile takip edilir.
# Yeni alan/tablo eklemek için listenin sonuna ekle — asla araya ekleme/silme.
_MIGRATIONS: list[tuple[int, str, str]] = [
    (1, "latency_ms kolonu (tool telemetrisi)", "ALTER TABLE events ADD COLUMN latency_ms INTEGER"),
    (2, "tokens kolonu (maliyet telemetrisi)", "ALTER TABLE events ADD COLUMN tokens INTEGER"),
]


def _run_migrations(conn: sqlite3.Connection) -> None:
    current = conn.execute("PRAGMA user_version").fetchone()[0]
    for version, desc, sql in _MIGRATIONS:
        if version <= current:
            continue
        try:
            conn.execute(sql)
            conn.execute(f"PRAGMA user_version = {version}")
        except sqlite3.OperationalError as e:
            # Kolon zaten varsa (elle eklenmiş) versiyonu yine de ilerlet
            if "duplicate column" in str(e).lower():
                conn.execute(f"PRAGMA user_version = {version}")
            else:
                raise


def _migrate_json_if_needed():
    """Eski JSON-per-day dosyalarını DB'ye aktar (yalnız bir kez)."""
    if not EPISODIC_DIR.exists():
        return
    flag = EPISODIC_DIR / ".migrated"
    if flag.exists():
        return
    imported = 0
    try:
        for f in sorted(EPISODIC_DIR.glob("*.json")):
            try:
                day = f.stem  # YYYY-MM-DD
                events = json.loads(f.read_text(encoding="utf-8"))
                if not isinstance(events, list):
                    continue
                for e in events:
                    hms = e.get("time", "00:00:00")
                    ts = f"{day}T{hms}"
                    meta = e.get("meta") or {}
                    tool = meta.get("tool") if isinstance(meta, dict) else None
                    ok = 1 if (isinstance(meta, dict) and meta.get("ok") != "0") else 0
                    if isinstance(meta, dict) and "ok" not in meta:
                        ok = 1
                    _conn.execute(
                        "INSERT INTO events (ts, day, hms, category, summary, mood, tool, ok, meta_json) "
                        "VALUES (?,?,?,?,?,?,?,?,?)",
                        (
                            ts, day, hms,
                            e.get("category", "interaction"),
                            (e.get("summary") or "")[:300],
                            e.get("mood") or None,
                            tool,
                            ok,
                            json.dumps(meta, ensure_ascii=False) if meta else None,
                        ),
                    )
                    imported += 1
            except Exception:
                continue
        flag.write_text(f"migrated {imported} events at {datetime.now().isoformat()}\n", encoding="utf-8")
    except Exception:
        pass


def log_event(summary: str, category: str = "interaction", mood: str = "",
              metadata: dict | None = None, latency_ms: int | None = None,
              tokens: int | None = None):
    now = datetime.now()
    day = now.strftime("%Y-%m-%d")
    hms = now.strftime("%H:%M:%S")
    ts = f"{day}T{hms}"
    tool = (metadata or {}).get("tool") if metadata else None
    ok = 1
    if metadata and metadata.get("ok") == "0":
        ok = 0
    with _lock:
        conn = _connect()
        conn.execute(
            "INSERT INTO events (ts, day, hms, category, summary, mood, tool, ok, meta_json, latency_ms, tokens) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (
                ts, day, hms, category,
                summary[:300],
                mood or None,
                tool,
                ok,
                json.dumps(metadata, ensure_ascii=False) if metadata else None,
                latency_ms,
                tokens,
            ),
        )


def log_command(tool_name: str, description: str = "", ok: bool = True,
                latency_ms: int | None = None):
    log_event(
        summary=f"Used {tool_name}: {description[:100]}",
        category="command" if ok else "command_error",
        metadata={"tool": tool_name, "ok": "1" if ok else "0"},
        latency_ms=latency_ms,
    )


def get_tool_telemetry(days: int = 7) -> list[dict]:
    """Tool başına ortalama latency, çağrı sayısı, başarı oranı."""
    from datetime import timedelta
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    with _lock:
        conn = _connect()
        rows = conn.execute(
            "SELECT tool, COUNT(*) n, "
            "       SUM(CASE WHEN ok=1 THEN 1 ELSE 0 END) ok_n, "
            "       AVG(latency_ms) avg_ms, MAX(latency_ms) max_ms "
            "FROM events WHERE tool IS NOT NULL AND day>=? "
            "GROUP BY tool ORDER BY n DESC",
            (cutoff,),
        ).fetchall()
    out = []
    for tool, n, ok_n, avg_ms, max_ms in rows:
        out.append({
            "tool": tool, "calls": n,
            "success_rate": round((ok_n or 0) * 100 / max(n, 1), 1),
            "avg_ms": round(avg_ms, 1) if avg_ms else None,
            "max_ms": max_ms,
        })
    return out


def get_today_summary() -> str:
    today = datetime.now().strftime("%Y-%m-%d")
    with _lock:
        conn = _connect()
        rows = conn.execute(
            "SELECT category, hms, summary FROM events WHERE day=? ORDER BY ts", (today,)
        ).fetchall()
    if not rows:
        return "Bugün henüz bir etkileşim kaydı yok."
    cats: dict[str, int] = {}
    for cat, _t, _s in rows:
        cats[cat] = cats.get(cat, 0) + 1
    lines = [f"📊 Bugünkü Aktivite ({len(rows)} olay, {rows[0][1]} - {rows[-1][1]}):"]
    for cat, count in cats.items():
        lines.append(f"  {cat}: {count}")
    lines.append("\n  Son olaylar:")
    for _c, hms, summary in rows[-5:]:
        lines.append(f"  [{hms}] {summary[:60]}")
    return "\n".join(lines)


def get_recent_context(hours: int = 2) -> str:
    cutoff_dt = datetime.now() - timedelta(hours=hours)
    cutoff_ts = cutoff_dt.strftime("%Y-%m-%dT%H:%M:%S")
    with _lock:
        conn = _connect()
        rows = conn.execute(
            "SELECT hms, summary FROM events WHERE ts >= ? ORDER BY ts DESC LIMIT 10",
            (cutoff_ts,),
        ).fetchall()
    if not rows:
        return ""
    rows = list(reversed(rows))
    lines = ["[RECENT ACTIVITY - last few hours]"]
    for hms, summary in rows:
        lines.append(f"  {hms}: {summary[:80]}")
    return "\n".join(lines)


def get_day_history(date_str: str) -> str:
    with _lock:
        conn = _connect()
        rows = conn.execute(
            "SELECT hms, mood, summary FROM events WHERE day=? ORDER BY ts", (date_str,)
        ).fetchall()
    if not rows:
        return f"{date_str} tarihinde kayıt bulunamadı."
    lines = [f"📅 {date_str} Geçmişi ({len(rows)} olay):"]
    for hms, mood, summary in rows:
        m = f" [{mood}]" if mood else ""
        lines.append(f"  [{hms}]{m} {summary[:80]}")
    return "\n".join(lines)


def get_available_days() -> list[str]:
    with _lock:
        conn = _connect()
        rows = conn.execute(
            "SELECT day FROM events GROUP BY day ORDER BY day DESC LIMIT 30"
        ).fetchall()
    return [r[0] for r in rows]


def cleanup_old(keep_days: int = 30) -> int:
    cutoff = (datetime.now() - timedelta(days=keep_days)).strftime("%Y-%m-%d")
    with _lock:
        conn = _connect()
        cur = conn.execute("DELETE FROM events WHERE day < ?", (cutoff,))
        removed = cur.rowcount or 0
        conn.execute("VACUUM")
    return removed


def get_tool_hints(days: int = 7, limit_per_tool: int = 1) -> str:
    """Son N gündeki başarılı tool kullanımlarından prompt'a ipucu çıkar."""
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    with _lock:
        conn = _connect()
        # En çok kullanılan 8 başarılı tool
        tools = conn.execute(
            "SELECT tool, COUNT(*) c FROM events "
            "WHERE category='command' AND ok=1 AND day>=? AND tool IS NOT NULL "
            "GROUP BY tool ORDER BY c DESC LIMIT 8",
            (cutoff,),
        ).fetchall()
        if not tools:
            return ""
        examples: dict[str, list[str]] = {}
        for tool, _c in tools:
            rows = conn.execute(
                "SELECT summary FROM events "
                "WHERE category='command' AND ok=1 AND tool=? AND day>=? "
                "ORDER BY ts DESC LIMIT ?",
                (tool, cutoff, limit_per_tool),
            ).fetchall()
            examples[tool] = [r[0].replace(f"Used {tool}: ", "")[:60] for r in rows]

    lines = ["[PROVEN TOOL PATTERNS — son işe yarayanlar]"]
    for tool, _c in tools:
        ex = "; ".join(examples.get(tool, [])) if examples.get(tool) else ""
        lines.append(f"  ✓ {tool}" + (f" — örn: {ex}" if ex else ""))
    return "\n".join(lines)
