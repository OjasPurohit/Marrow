"""Import bundled offline catalog into the user database (once per catalog revision)."""

from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path

from marrow.core.paths import bundled_foods_catalog_path
from marrow.data.foods.nutrients import NUTRIENT_COLUMN_NAMES

META_KEY = "foods_catalog_seed_digest"


def _catalog_digest(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha256(data).hexdigest()


def _meta_get(conn: sqlite3.Connection, key: str) -> str | None:
    row = conn.execute("SELECT value FROM app_meta WHERE key = ?", (key,)).fetchone()
    return str(row[0]) if row else None


def _meta_set(conn: sqlite3.Connection, key: str, value: str) -> None:
    conn.execute(
        """
        INSERT INTO app_meta (key, value) VALUES (?, ?)
        ON CONFLICT (key) DO UPDATE SET value = excluded.value
        """,
        (key, value),
    )


def catalog_seed_status(conn: sqlite3.Connection) -> dict[str, str | int | bool]:
    bundled = bundled_foods_catalog_path()
    digest = _catalog_digest(bundled) if bundled.exists() else ""
    stored = _meta_get(conn, META_KEY)
    count = conn.execute("SELECT COUNT(*) FROM foods WHERE source != 'custom'").fetchone()[0]
    return {
        "bundled_path": str(bundled),
        "bundled_exists": bundled.exists(),
        "stored_digest": stored or "",
        "current_digest": digest,
        "catalog_food_count": int(count),
        "needs_seed": bundled.exists() and stored != digest,
    }


def ensure_catalog_seeded(conn: sqlite3.Connection) -> int:
    """
    Copy foods from bundled SQLite into the user DB when the bundle changes.
    Returns number of foods imported (0 if already up to date).
    """
    bundled = bundled_foods_catalog_path()
    if not bundled.exists():
        return 0

    digest = _catalog_digest(bundled)
    if _meta_get(conn, META_KEY) == digest:
        return 0

    imported = _import_bundled_catalog(conn, bundled)
    _meta_set(conn, META_KEY, digest)
    conn.commit()
    return imported


def _import_bundled_catalog(conn: sqlite3.Connection, bundled_path: Path) -> int:
    """Merge bundled catalog rows into user DB (catalog sources only)."""
    uri = f"file:{bundled_path.resolve()}?mode=ro"
    conn.execute("ATTACH DATABASE ? AS bundled", (uri,))
    try:
        sources = ("usda", "off", "ifct", "sample")
        placeholders = ", ".join("?" for _ in sources)
        existing = conn.execute(
            f"""
            SELECT source, source_food_id FROM foods
            WHERE source IN ({placeholders})
            """,
            sources,
        ).fetchall()
        existing_keys = {(r[0], r[1]) for r in existing}

        rows = conn.execute(
            f"""
            SELECT id, source, source_food_id, name, name_normalized, basis,
                   preparation, data_quality, brand, barcode, locale
            FROM bundled.foods
            WHERE source IN ({placeholders})
            """,
            sources,
        ).fetchall()

        nutrient_cols = ", ".join(NUTRIENT_COLUMN_NAMES)
        imported = 0
        for row in rows:
            key = (row["source"], row["source_food_id"])
            if key in existing_keys:
                continue
            cur = conn.execute(
                """
                INSERT INTO foods (
                    source, source_food_id, name, name_normalized, basis,
                    preparation, data_quality, brand, barcode, locale
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                RETURNING id
                """,
                (
                    row["source"],
                    row["source_food_id"],
                    row["name"],
                    row["name_normalized"],
                    row["basis"],
                    row["preparation"],
                    row["data_quality"],
                    row["brand"],
                    row["barcode"],
                    row["locale"],
                ),
            )
            new_id = int(cur.fetchone()[0])
            bundled_food_id = int(row["id"])

            n = conn.execute(
                f"SELECT {nutrient_cols} FROM bundled.food_nutrients WHERE food_id = ?",
                (bundled_food_id,),
            ).fetchone()
            if n:
                conn.execute(
                    f"""
                    INSERT INTO food_nutrients (food_id, {nutrient_cols})
                    VALUES (?, {", ".join("?" for _ in NUTRIENT_COLUMN_NAMES)})
                    """,
                    (new_id, *[n[c] for c in NUTRIENT_COLUMN_NAMES]),
                )

            servings = conn.execute(
                """
                SELECT label, amount, unit, grams_equivalent, is_default, sort_order
                FROM bundled.food_servings WHERE food_id = ?
                ORDER BY sort_order
                """,
                (bundled_food_id,),
            ).fetchall()
            for s in servings:
                conn.execute(
                    """
                    INSERT INTO food_servings (
                        food_id, label, amount, unit, grams_equivalent, is_default, sort_order
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        new_id,
                        s["label"],
                        s["amount"],
                        s["unit"],
                        s["grams_equivalent"],
                        s["is_default"],
                        s["sort_order"],
                    ),
                )
            imported += 1
        conn.commit()
        return imported
    finally:
        conn.commit()
        conn.execute("DETACH DATABASE bundled")
