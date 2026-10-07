"""Recipe CRUD and per-serving nutrient aggregation."""

from __future__ import annotations

import sqlite3
from typing import Any

from marrow.data.foods.nutrients import NUTRIENT_COLUMN_NAMES
from marrow.data.foods.units import scale_nutrients
from marrow.data.ingest.normalize import normalize_food_name
from marrow.services.food_repository import fetch_nutrients


def _sum_nutrients(rows: list[dict[str, float | None]]) -> dict[str, float | None]:
    totals: dict[str, float] = {}
    for row in rows:
        for key in NUTRIENT_COLUMN_NAMES:
            value = row.get(key)
            if value is None:
                continue
            totals[key] = totals.get(key, 0.0) + float(value)
    return {k: totals.get(k) for k in NUTRIENT_COLUMN_NAMES}


def aggregate_recipe_nutrients(
    conn: sqlite3.Connection,
    ingredients: list[dict[str, Any]],
) -> dict[str, float | None]:
    """Sum scaled nutrients for ingredient list [{food_id, grams}, ...]."""
    scaled_rows: list[dict[str, float | None]] = []
    for item in ingredients:
        food_id = int(item["food_id"])
        grams = float(item["grams"])
        if grams <= 0:
            raise ValueError("ingredient grams must be positive")
        row = conn.execute("SELECT basis FROM foods WHERE id = ?", (food_id,)).fetchone()
        if not row:
            raise ValueError(f"unknown food_id {food_id}")
        per_100 = fetch_nutrients(conn, food_id)
        scaled_rows.append(scale_nutrients(per_100, grams, row["basis"]))
    return _sum_nutrients(scaled_rows)


def create_recipe(
    conn: sqlite3.Connection,
    name: str,
    servings_count: float,
    ingredients: list[dict[str, Any]],
    notes: str | None = None,
) -> dict:
    clean = name.strip()
    if not clean:
        raise ValueError("name is required")
    if servings_count <= 0:
        raise ValueError("servings_count must be positive")
    if not ingredients:
        raise ValueError("at least one ingredient is required")

    aggregate_recipe_nutrients(conn, ingredients)

    cur = conn.execute(
        """
        INSERT INTO recipes (name, name_normalized, servings_count, notes)
        VALUES (?, ?, ?, ?)
        RETURNING id
        """,
        (clean, normalize_food_name(clean), servings_count, notes),
    )
    recipe_id = int(cur.fetchone()[0])

    for idx, item in enumerate(ingredients):
        conn.execute(
            """
            INSERT INTO recipe_ingredients (recipe_id, food_id, grams, sort_order, note)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                recipe_id,
                int(item["food_id"]),
                float(item["grams"]),
                idx,
                item.get("note"),
            ),
        )
    conn.commit()

    recipe = get_recipe(conn, recipe_id)
    assert recipe is not None
    return recipe


def get_recipe(conn: sqlite3.Connection, recipe_id: int) -> dict | None:
    row = conn.execute("SELECT * FROM recipes WHERE id = ?", (recipe_id,)).fetchone()
    if not row:
        return None
    ingredients = conn.execute(
        """
        SELECT ri.id, ri.food_id, ri.grams, ri.note, ri.sort_order, f.name AS food_name
        FROM recipe_ingredients ri
        JOIN foods f ON f.id = ri.food_id
        WHERE ri.recipe_id = ?
        ORDER BY ri.sort_order, ri.id
        """,
        (recipe_id,),
    ).fetchall()
    ing_list = [
        {
            "id": int(r["id"]),
            "food_id": int(r["food_id"]),
            "food_name": r["food_name"],
            "grams": float(r["grams"]),
            "note": r["note"],
            "sort_order": int(r["sort_order"]),
        }
        for r in ingredients
    ]
    total = aggregate_recipe_nutrients(
        conn,
        [{"food_id": i["food_id"], "grams": i["grams"]} for i in ing_list],
    )
    servings = float(row["servings_count"])
    per_serving = {
        k: (None if v is None else round(v / servings, 4))
        for k, v in total.items()
    }
    return {
        "id": int(row["id"]),
        "name": row["name"],
        "servings_count": servings,
        "notes": row["notes"],
        "ingredients": ing_list,
        "nutrients_total": total,
        "nutrients_per_serving": per_serving,
    }
