"""User-defined custom foods (per 100g / 100ml)."""

from __future__ import annotations

import sqlite3
import uuid
from typing import Any

from marrow.data.foods.nutrients import NUTRIENT_COLUMN_NAMES, NutrientValues
from marrow.data.ingest.normalize import normalize_food_name
from marrow.services.food_repository import fetch_nutrients, fetch_servings


def create_custom_food(
    conn: sqlite3.Connection,
    name: str,
    nutrients: dict[str, Any],
    *,
    basis: str = "per_100g",
    preparation: str = "unknown",
    brand: str | None = None,
) -> dict:
    if basis not in ("per_100g", "per_100ml"):
        raise ValueError("basis must be per_100g or per_100ml")
    if preparation not in ("raw", "cooked", "unknown"):
        raise ValueError("invalid preparation")

    clean_name = name.strip()
    if not clean_name:
        raise ValueError("name is required")

    nv = NutrientValues()
    for key, raw in nutrients.items():
        if key not in NUTRIENT_COLUMN_NAMES:
            continue
        if raw is None:
            continue
        setattr(nv, key, float(raw))

    source_id = f"custom-{uuid.uuid4().hex[:12]}"
    cur = conn.execute(
        """
        INSERT INTO foods (
            source, source_food_id, name, name_normalized, basis,
            preparation, data_quality, brand
        ) VALUES ('custom', ?, ?, ?, ?, ?, 'estimated', ?)
        RETURNING id
        """,
        (
            source_id,
            clean_name,
            normalize_food_name(clean_name),
            basis,
            preparation,
            brand,
        ),
    )
    food_id = int(cur.fetchone()[0])
    n = nv.as_dict()
    cols = ", ".join(NUTRIENT_COLUMN_NAMES)
    conn.execute(
        f"""
        INSERT INTO food_nutrients (food_id, {cols})
        VALUES (?, {", ".join("?" for _ in NUTRIENT_COLUMN_NAMES)})
        """,
        (food_id, *[n[c] for c in NUTRIENT_COLUMN_NAMES]),
    )
    conn.execute(
        """
        INSERT INTO food_servings (
            food_id, label, amount, unit, grams_equivalent, is_default, sort_order
        ) VALUES (?, '100 g', 100, 'g', 100, 1, 0)
        """,
        (food_id,),
    )
    conn.commit()
    return {
        "id": food_id,
        "name": clean_name,
        "source": "custom",
        "basis": basis,
        "preparation": preparation,
        "brand": brand,
        "nutrients_per_100": fetch_nutrients(conn, food_id),
        "servings": fetch_servings(conn, food_id),
    }
