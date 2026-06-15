# ADR 0001 — SQLite for vector memory, not ChromaDB

- **Status:** Accepted
- **Date:** 2026-06-11

## Context

For semantic recall (RAG) we need to store embeddings and run similarity search.
Options: ChromaDB, FAISS, sqlite-vec, or plain SQLite + numpy.

## Decision

We use **plain SQLite (BLOB column) + numpy cosine**.

## Rationale

- **Zero extra service** — SQLite is in the stdlib; ChromaDB is a separate dependency, sometimes a separate process
- **Sufficient scale** — ~10K records is typical for a personal assistant; 768-dim × 10K ≈ 30MB matrix, numpy matmul <5ms
- **Single file** — easy backup/migration, consistent with the existing episodic.db pattern
- **Dependency weight** — ChromaDB pulls onnxruntime + tokenizers (~100MB), against our RAM target

## Consequences

- If linear scan slows down past 10K+ records, we can switch to the `sqlite-vec` extension or FAISS (columns are compatible)
- Embedding generation depends on the Gemini API (won't work offline) — accepted, the Live API is online anyway
- `recall()` loads the last 5000 rows per call; there's an indexed `kind` filter

## Alternatives

- **ChromaDB** — more features but heavy, overkill for our scale
- **FAISS** — fast but C++ dependency + separate index file management
- **sqlite-vec** — a good middle ground; first choice once scale demands it
