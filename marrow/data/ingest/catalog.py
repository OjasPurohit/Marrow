"""Write FoodRecord batches into a SQLite foods catalog."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from marrow.data.foods.nutrients import NUTRIENT_COLUMN_NAMES
from marrow.data.ingest.models import FoodRecord
from marrow.data.ingest.normalize import normalize_food_name
from marrow.data.migrator import migrate


def open_catalog(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    migrate(conn)
    return conn


def upsert_foods(conn: sqlite3.Connection, records: list[FoodRecord]) -> int:
    inserted = 0
    nutrient_cols = ", ".join(NUTRIENT_COLUMN_NAMES)
    nutrient_placeholders = ", ".join("?" for _ in NUTRIENT_COLUMN_NAMES)
    for rec in records:
        cur = conn.execute(
            """
            INSERT INTO foods (
                source, source_food_id, name, name_normalized, basis,
                preparation, data_quality, brand, barcode, locale
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (source, source_food_id) DO UPDATE SET
                name = excluded.name,
                name_normalized = excluded.name_normalized,
                basis = excluded.basis,
                preparation = excluded.preparation,
                data_quality = excluded.data_quality,
                brand = excluded.brand,
                barcode = excluded.barcode,
                locale = excluded.locale
            RETURNING id
            """,
            (
                rec.source,
                rec.source_food_id,
                rec.name,
                normalize_food_name(rec.name),
                rec.basis,
                rec.preparation,
                rec.data_quality,
                rec.brand,
                rec.barcode,
                rec.locale,
            ),
        )
        row = cur.fetchone()
        food_id = int(row[0])
        inserted += 1

        n = rec.nutrients.as_dict()
        conn.execute(
            f"""
            INSERT INTO food_nutrients (food_id, {nutrient_cols})
            VALUES (?, {nutrient_placeholders})
            ON CONFLICT (food_id) DO UPDATE SET
            {", ".join(f"{c} = excluded.{c}" for c in NUTRIENT_COLUMN_NAMES)}
            """,
            (food_id, *[n[c] for c in NUTRIENT_COLUMN_NAMES]),
        )

        conn.execute("DELETE FROM food_servings WHERE food_id = ?", (food_id,))
        for serving in rec.servings:
            conn.execute(
                """
                INSERT INTO food_servings (
                    food_id, label, amount, unit, grams_equivalent, is_default, sort_order
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    food_id,
                    serving.label,
                    serving.amount,
                    serving.unit,
                    serving.grams_equivalent,
                    1 if serving.is_default else 0,
                    serving.sort_order,
                ),
            )
    conn.commit()
    return inserted


def catalog_stats(conn: sqlite3.Connection) -> dict[str, int]:
    foods = conn.execute("SELECT COUNT(*) FROM foods").fetchone()[0]
    servings = conn.execute("SELECT COUNT(*) FROM food_servings").fetchone()[0]
    by_source = {
        row[0]: row[1]
        for row in conn.execute(
            "SELECT source, COUNT(*) FROM foods GROUP BY source ORDER BY source"
        )
    }
    return {"foods": foods, "servings": servings, "by_source": by_source}
