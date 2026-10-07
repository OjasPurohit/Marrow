"""Food detail and serving conversion."""

from __future__ import annotations

import sqlite3

from marrow.data.foods.units import convert_to_basis_amount, scale_nutrients
from marrow.services.food_repository import (
    fetch_food_row,
    fetch_nutrients,
    fetch_servings,
    touch_recent,
)


def get_food_detail(conn: sqlite3.Connection, food_id: int) -> dict | None:
    row = fetch_food_row(conn, food_id)
    if not row:
        return None
    touch_recent(conn, food_id)
    conn.commit()
    nutrients = fetch_nutrients(conn, food_id)
    servings = fetch_servings(conn, food_id)
    is_fav = conn.execute(
        "SELECT 1 FROM food_favorites WHERE food_id = ?",
        (food_id,),
    ).fetchone()
    return {
        "id": int(row["id"]),
        "name": row["name"],
        "source": row["source"],
        "brand": row["brand"],
        "basis": row["basis"],
        "preparation": row["preparation"],
        "data_quality": row["data_quality"],
        "barcode": row["barcode"],
        "locale": row["locale"],
        "nutrients_per_100": nutrients,
        "servings": servings,
        "is_favorite": bool(is_fav),
    }


def convert_food_serving(
    conn: sqlite3.Connection,
    food_id: int,
    amount: float,
    unit: str,
    target_preparation: str | None = None,
) -> dict:
    row = fetch_food_row(conn, food_id)
    if not row:
        raise ValueError("food not found")
    servings = fetch_servings(conn, food_id)
    conversion = convert_to_basis_amount(
        float(amount),
        unit,
        basis=row["basis"],
        food_name=row["name"],
        preparation=row["preparation"],
        food_servings=servings,
        target_preparation=target_preparation,
    )
    per_100 = fetch_nutrients(conn, food_id)
    scaled = scale_nutrients(per_100, conversion.basis_amount, row["basis"])
    return {
        "food_id": food_id,
        "amount": conversion.amount,
        "unit": conversion.unit,
        "grams_equivalent": conversion.grams_equivalent,
        "basis_amount": conversion.basis_amount,
        "basis": conversion.basis,
        "matched_food_serving": conversion.matched_food_serving,
        "note": conversion.note,
        "nutrients": scaled,
    }
