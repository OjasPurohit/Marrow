"""Body weight log storage (M6); trend smoothing for M9 UI."""

from __future__ import annotations

import sqlite3
from datetime import date
from typing import Any


def add_weight_entry(
    conn: sqlite3.Connection,
    weight_kg: float,
    logged_date: str | None = None,
    note: str | None = None,
) -> dict:
    if weight_kg <= 0:
        raise ValueError("weight_kg must be positive")
    day = logged_date or date.today().isoformat()
    cur = conn.execute(
        """
        INSERT INTO weight_log (logged_date, weight_kg, note)
        VALUES (?, ?, ?)
        """,
        (day, float(weight_kg), note),
    )
    conn.commit()
    return {
        "id": int(cur.lastrowid),
        "logged_date": day,
        "weight_kg": float(weight_kg),
        "note": note,
    }


def list_weight_entries(
    conn: sqlite3.Connection,
    limit: int = 90,
) -> list[dict]:
    rows = conn.execute(
        """
        SELECT id, logged_date, weight_kg, note, created_at
        FROM weight_log
        ORDER BY logged_date DESC, id DESC
        LIMIT ?
        """,
        (int(limit),),
    ).fetchall()
    return [
        {
            "id": int(row["id"]),
            "logged_date": row["logged_date"],
            "weight_kg": float(row["weight_kg"]),
            "note": row["note"],
            "created_at": row["created_at"],
        }
        for row in rows
    ]


def delete_weight_entry(conn: sqlite3.Connection, entry_id: int) -> dict:
    cur = conn.execute("DELETE FROM weight_log WHERE id = ?", (int(entry_id),))
    conn.commit()
    if cur.rowcount == 0:
        raise ValueError(f"weight entry not found: {entry_id}")
    return {"deleted": True, "id": int(entry_id)}


def smooth_weight_trend(
    points: list[dict[str, Any]],
    window: int = 7,
) -> list[float | None]:
    """
    Simple trailing moving average on logged weights (calendar-aligned rows).

    Rows with missing weight_kg stay null in the output until a window has data.
    """
    if window < 1:
        raise ValueError("window must be at least 1")
    values: list[float | None] = []
    for point in points:
        raw = point.get("weight_kg")
        values.append(float(raw) if raw is not None else None)

    smoothed: list[float | None] = []
    for idx in range(len(values)):
        slice_start = max(0, idx - window + 1)
        chunk = [v for v in values[slice_start : idx + 1] if v is not None]
        if not chunk:
            smoothed.append(None)
        else:
            smoothed.append(round(sum(chunk) / len(chunk), 2))
    return smoothed


def get_weight_log_with_trend(
    conn: sqlite3.Connection,
    limit: int = 90,
) -> dict:
    entries = list_weight_entries(conn, limit=limit)
    chronological = list(reversed(entries))
    smooth = smooth_weight_trend(chronological, window=7)
    for idx, entry in enumerate(chronological):
        entry["smooth_kg"] = smooth[idx]
    return {
        "entries": list(reversed(chronological)),
        "window_days": 7,
    }
