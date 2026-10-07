"""Body weight log storage (M6)."""

from __future__ import annotations

import sqlite3
from datetime import date


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
