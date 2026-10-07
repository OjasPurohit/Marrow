"""FTS5 food search."""

from __future__ import annotations

import re
import sqlite3
import time

from marrow.services.food_repository import row_to_food_summary

_MAX_QUERY_LEN = 80


def _fts_query(raw: str) -> str:
    """Build a prefix FTS5 query from user input."""
    text = raw.strip()
    if not text:
        return ""
    text = re.sub(r"[^\w\s\-']+", " ", text, flags=re.UNICODE)
    tokens = [t for t in text.split() if t]
    if not tokens:
        return ""
    parts = []
    for tok in tokens[:8]:
        escaped = tok.replace('"', '""')
        parts.append(f'"{escaped}"*')
    return " ".join(parts)


def search_foods(
    conn: sqlite3.Connection,
    query: str,
    limit: int = 25,
) -> dict:
    started = time.perf_counter()
    limit = max(1, min(int(limit), 50))
    q = _fts_query(query)
    if not q:
        return {"query": query, "results": [], "elapsed_ms": 0.0}

    rows = conn.execute(
        """
        SELECT f.id, f.name, f.source, f.brand, f.basis, f.preparation,
               f.data_quality, f.barcode,
               bm25(foods_fts) AS rank
        FROM foods_fts
        JOIN foods f ON f.id = foods_fts.rowid
        WHERE foods_fts MATCH ?
        ORDER BY rank
        LIMIT ?
        """,
        (q, limit),
    ).fetchall()

    elapsed_ms = (time.perf_counter() - started) * 1000.0
    results = [row_to_food_summary(r) | {"rank": float(r["rank"])} for r in rows]
    return {
        "query": query,
        "results": results,
        "elapsed_ms": round(elapsed_ms, 2),
    }
