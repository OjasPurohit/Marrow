"""Shared DB helpers for food reads."""

from __future__ import annotations

import sqlite3

from marrow.data.foods.nutrients import NUTRIENT_COLUMN_NAMES


def row_to_food_summary(row: sqlite3.Row) -> dict:
    return {
        "id": int(row["id"]),
        "name": row["name"],
        "source": row["source"],
        "brand": row["brand"],
        "basis": row["basis"],
        "preparation": row["preparation"],
        "data_quality": row["data_quality"],
        "barcode": row["barcode"],
    }


def fetch_food_row(conn: sqlite3.Connection, food_id: int) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM foods WHERE id = ?", (food_id,)).fetchone()


def fetch_nutrients(conn: sqlite3.Connection, food_id: int) -> dict[str, float | None]:
    cols = ", ".join(NUTRIENT_COLUMN_NAMES)
    row = conn.execute(
        f"SELECT {cols} FROM food_nutrients WHERE food_id = ?",
        (food_id,),
    ).fetchone()
    if not row:
        return {c: None for c in NUTRIENT_COLUMN_NAMES}
    return {c: row[c] for c in NUTRIENT_COLUMN_NAMES}


def fetch_servings(conn: sqlite3.Connection, food_id: int) -> list[dict]:
    rows = conn.execute(
        """
        SELECT id, label, amount, unit, grams_equivalent, is_default, sort_order
        FROM food_servings
        WHERE food_id = ?
        ORDER BY sort_order, id
        """,
        (food_id,),
    ).fetchall()
    return [
        {
            "id": int(r["id"]),
            "label": r["label"],
            "amount": float(r["amount"]),
            "unit": r["unit"],
            "grams_equivalent": float(r["grams_equivalent"]),
            "is_default": bool(r["is_default"]),
            "sort_order": int(r["sort_order"]),
        }
        for r in rows
    ]


def touch_recent(conn: sqlite3.Connection, food_id: int) -> None:
    conn.execute(
        """
        INSERT INTO food_recents (food_id, last_used_at, use_count)
        VALUES (?, datetime('now'), 1)
        ON CONFLICT (food_id) DO UPDATE SET
            last_used_at = datetime('now'),
            use_count = food_recents.use_count + 1
        """,
        (food_id,),
    )
