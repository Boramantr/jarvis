"""Vector Memory — Semantik geri çağırma (RAG).

JARVIS'in "gerçekten hatırlama" katmanı. Her önemli olay/konuşma parçası
Gemini gemini-embedding-001 ile 768-dim vektöre dönüştürülüp SQLite BLOB'una
yazılır. Geri çağırma sırasında sorgu embedding'i üretilir, kosinüs benzerliği
ile top-k sonuç döner.

Dış API (geriye uyumlu hedeflenir):
    remember(text, kind="note", meta=None)  -> id
    recall(query, k=5)                      -> [(score, text, meta), ...]
    forget(id) / clear()
    stats() -> dict

Tasarım kararları:
- Tek SQLite DB (vectors.db), tek tablo `vectors(id, text, kind, ts, vec BLOB)`.
- Gemini embeddings (`gemini-embedding-001`) — API key zaten var, lokal model
  yüklemiyoruz (RAM'e iyi).
- Embedding tarafında 60sn LRU cache + 30 günlük "stale" temizlik (cleanup).
- 10K kayda kadar numpy cosine yeterince hızlı; ileride sqlite-vec'e geçilebilir.
"""
from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np

DB_PATH = Path.home() / ".jarvis" / "memory" / "vectors.db"
_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "api_keys.json"
_MODEL = "gemini-embedding-001"
_DIM = 768
_lock = threading.Lock()
_conn: sqlite3.Connection | None = None
_client = None
_embed_cache: dict[str, np.ndarray] = {}
_embed_cache_max = 256


def _client_lazy():
    """Gemini client lazy init — modül import maliyeti düşük kalsın."""
    global _client
    if _client is not None:
        return _client
    from google import genai
    try:
        from core.config import settings
        key = settings.resolve_api_key()
    except Exception:
        key = json.loads(_CONFIG_PATH.read_text(encoding="utf-8"))["gemini_api_key"]
    _client = genai.Client(api_key=key)
    return _client


def _connect() -> sqlite3.Connection:
    global _conn
    if _conn is not None:
        return _conn
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    _conn = sqlite3.connect(str(DB_PATH), check_same_thread=False, isolation_level=None)
    _conn.execute("PRAGMA journal_mode=WAL")
    _conn.execute("PRAGMA synchronous=NORMAL")
    _conn.execute(
        """CREATE TABLE IF NOT EXISTS vectors (
            id    INTEGER PRIMARY KEY AUTOINCREMENT,
            text  TEXT NOT NULL,
            kind  TEXT NOT NULL,
            ts    TEXT NOT NULL,
            meta  TEXT,
            vec   BLOB NOT NULL
        )"""
    )
    _conn.execute("CREATE INDEX IF NOT EXISTS idx_vec_kind ON vectors(kind)")
    _conn.execute("CREATE INDEX IF NOT EXISTS idx_vec_ts ON vectors(ts)")
    return _conn


def _embed(text: str) -> np.ndarray:
    """Tek bir metin → 768-dim numpy float32 vektör. LRU cache'li."""
    text = text.strip()
    if not text:
        return np.zeros(_DIM, dtype=np.float32)
    if text in _embed_cache:
        return _embed_cache[text]
    client = _client_lazy()
    resp = client.models.embed_content(model=_MODEL, contents=text)
    # google-genai sürümleri arası uyum
    if hasattr(resp, "embeddings") and resp.embeddings:
        values = resp.embeddings[0].values
    else:
        values = resp.embedding.values  # type: ignore[attr-defined]
    vec = np.asarray(values, dtype=np.float32)
    n = np.linalg.norm(vec)
    if n > 0:
        vec = vec / n
    if len(_embed_cache) >= _embed_cache_max:
        _embed_cache.pop(next(iter(_embed_cache)))
    _embed_cache[text] = vec
    return vec


def _embed_batch(texts: list[str]) -> list[np.ndarray]:
    out = []
    for t in texts:
        try:
            out.append(_embed(t))
        except Exception:
            out.append(np.zeros(_DIM, dtype=np.float32))
    return out


def remember(text: str, kind: str = "note", meta: dict | None = None) -> int:
    """Yeni bir kayıt ekle. Aynı metin daha önce kaydedildiyse re-embed etmez."""
    text = (text or "").strip()
    if not text:
        return -1
    if len(text) > 4000:
        text = text[:4000]
    try:
        vec = _embed(text)
    except Exception:
        return -1
    with _lock:
        conn = _connect()
        cur = conn.execute(
            "INSERT INTO vectors (text, kind, ts, meta, vec) VALUES (?,?,?,?,?)",
            (
                text,
                kind,
                datetime.now().isoformat(timespec="seconds"),
                json.dumps(meta, ensure_ascii=False) if meta else None,
                vec.tobytes(),
            ),
        )
        return cur.lastrowid or -1


def recall(query: str, k: int = 5, kind: str | None = None,
           min_score: float = 0.55) -> list[tuple[float, str, dict | None]]:
    """Sorgu için en benzer k kaydı döndürür.
    min_score altındaki sonuçlar elenir — gürültü engellenir.
    """
    query = (query or "").strip()
    if not query:
        return []
    try:
        q = _embed(query)
    except Exception:
        return []
    with _lock:
        conn = _connect()
        if kind:
            rows = conn.execute(
                "SELECT id, text, meta, vec FROM vectors WHERE kind=? ORDER BY id DESC LIMIT 5000",
                (kind,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT id, text, meta, vec FROM vectors ORDER BY id DESC LIMIT 5000"
            ).fetchall()
    if not rows:
        return []
    mat = np.frombuffer(b"".join(r[3] for r in rows), dtype=np.float32).reshape(-1, _DIM)
    scores = mat @ q  # cosine — both normalized
    order = np.argsort(-scores)[:k]
    out: list[tuple[float, str, dict | None]] = []
    for idx in order:
        s = float(scores[idx])
        if s < min_score:
            continue
        _id, text, meta_json, _v = rows[idx]
        meta = json.loads(meta_json) if meta_json else None
        out.append((s, text, meta))
    return out


def forget(record_id: int) -> bool:
    with _lock:
        cur = _connect().execute("DELETE FROM vectors WHERE id=?", (record_id,))
        return (cur.rowcount or 0) > 0


def clear(kind: str | None = None) -> int:
    with _lock:
        conn = _connect()
        if kind:
            cur = conn.execute("DELETE FROM vectors WHERE kind=?", (kind,))
        else:
            cur = conn.execute("DELETE FROM vectors")
        conn.execute("VACUUM")
        return cur.rowcount or 0


def cleanup_old(keep_days: int = 180) -> int:
    cutoff = (datetime.now() - timedelta(days=keep_days)).isoformat()
    with _lock:
        cur = _connect().execute("DELETE FROM vectors WHERE ts < ?", (cutoff,))
        return cur.rowcount or 0


def stats() -> dict:
    with _lock:
        conn = _connect()
        total = conn.execute("SELECT COUNT(*) FROM vectors").fetchone()[0]
        by_kind = dict(conn.execute(
            "SELECT kind, COUNT(*) FROM vectors GROUP BY kind"
        ).fetchall())
    return {"total": total, "by_kind": by_kind, "embed_cache": len(_embed_cache)}


def get_context_for_prompt(query: str, k: int = 3) -> str:
    """Prompt'a enjekte için kısa formatta."""
    hits = recall(query, k=k)
    if not hits:
        return ""
    lines = ["[SEMANTIC RECALL — geçmişten ilgili kayıtlar]"]
    for score, text, _meta in hits:
        snippet = text.replace("\n", " ")[:140]
        lines.append(f"  ({score:.2f}) {snippet}")
    return "\n".join(lines)
