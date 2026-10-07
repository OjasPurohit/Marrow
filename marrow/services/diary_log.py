"""Persist confirmed diary log entries and list daily logs."""

from __future__ import annotations

import sqlite3
from datetime import date

from marrow.services.food_detail import convert_food_serving
from marrow.services.food_repository import fetch_food_row
from marrow.services.diary_totals import (
    PLACEHOLDER_DAILY_TARGETS,
    group_entries_by_meal,
    remaining_budget,
    summarize_diary_nutrients,
)
from marrow.services.nutrient_validation import collect_nutrient_warnings, nutrients_for_display

MEAL_TAGS = frozenset(
    {"breakfast", "lunch", "dinner", "snack", "pre_workout", "post_workout"}
)


def _local_today() -> str:
    return date.today().isoformat()


def _normalize_meal_tag(tag: str | None) -> str:
    value = (tag or "snack").strip().lower()
    return value if value in MEAL_TAGS else "snack"


def confirm_and_save_log(conn: sqlite3.Connection, payload: dict) -> dict:
    log_date = str(payload.get("log_date") or _local_today())
    meal_tag = _normalize_meal_tag(payload.get("meal_tag"))
    source_text = payload.get("source_text")
    items = list(payload.get("items") or [])
    if not items:
        raise ValueError("at least one item is required")

    cur = conn.execute(
        """
        INSERT INTO diary_logs (log_date, meal_tag, source_text)
        VALUES (?, ?, ?)
        """,
        (log_date, meal_tag, source_text),
    )
    log_id = int(cur.lastrowid)

    saved: list[dict] = []
    for position, item in enumerate(items):
        food_id = int(item["food_id"])
        row = fetch_food_row(conn, food_id)
        if not row:
            raise ValueError(f"food not found: {food_id}")
        amount = float(item.get("amount") or 1)
        unit = str(item.get("unit") or "serving")
        confidence = str(item.get("match_confidence") or "ESTIMATED").upper()
        if confidence not in ("EXACT", "GOOD", "ESTIMATED"):
            confidence = "ESTIMATED"

        converted = convert_food_serving(conn, food_id, amount, unit)
        nutrients = nutrients_for_display(converted["nutrients"])
        warnings = collect_nutrient_warnings(
            energy_kcal=nutrients.get("energy_kcal"),
            protein_g=nutrients.get("protein_g"),
            carbs_g=nutrients.get("carbs_g"),
            fat_g=nutrients.get("fat_g"),
            grams_equivalent=float(converted["grams_equivalent"]),
            serving_note=converted.get("note"),
        )

        entry_cur = conn.execute(
            """
            INSERT INTO diary_log_entries (
                log_id, food_id, food_name, amount, unit, grams_equivalent,
                energy_kcal, protein_g, carbs_g, fat_g,
                match_confidence, raw_fragment, position
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                log_id,
                food_id,
                row["name"],
                float(converted["amount"]),
                converted["unit"],
                float(converted["grams_equivalent"]),
                nutrients.get("energy_kcal"),
                nutrients.get("protein_g"),
                nutrients.get("carbs_g"),
                nutrients.get("fat_g"),
                confidence,
                item.get("raw_fragment"),
                position,
            ),
        )
        saved.append(
            {
                "entry_id": int(entry_cur.lastrowid),
                "food_id": food_id,
                "food_name": row["name"],
                "amount": float(converted["amount"]),
                "unit": converted["unit"],
                "grams_equivalent": float(converted["grams_equivalent"]),
                "energy_kcal": nutrients.get("energy_kcal"),
                "nutrients": nutrients,
                "match_confidence": confidence,
                "warnings": warnings,
            }
        )

    conn.commit()
    totals = _totals_payload(saved)
    return {
        "log_id": log_id,
        "log_date": log_date,
        "meal_tag": meal_tag,
        "entries": saved,
        "totals": totals,
    }


def _totals_payload(entries: list[dict]) -> dict:
    nutrients = summarize_diary_nutrients(entries)
    return {
        **nutrients,
        "entry_count": len(entries),
        "targets": dict(PLACEHOLDER_DAILY_TARGETS),
        "remaining": remaining_budget(nutrients),
    }


def summarize_entries(entries: list[dict]) -> dict:
    """Backward-compatible summary for a single save batch."""
    nutrients = summarize_diary_nutrients(entries)
    return {**nutrients, "entry_count": len(entries)}


def get_daily_nutrient_totals(
    conn: sqlite3.Connection,
    log_date: str | None = None,
) -> dict:
    day = list_diary_entries_for_date(conn, log_date)
    return {
        "log_date": day["log_date"],
        "totals": day["totals"],
        "meals": day["meals"],
    }


def list_diary_entries_for_date(
    conn: sqlite3.Connection,
    log_date: str | None = None,
) -> dict:
    day = log_date or _local_today()
    rows = conn.execute(
        """
        SELECT
            e.id AS entry_id,
            e.log_id,
            l.meal_tag,
            l.created_at AS log_created_at,
            e.food_id,
            e.food_name,
            e.amount,
            e.unit,
            e.grams_equivalent,
            e.energy_kcal,
            e.protein_g,
            e.carbs_g,
            e.fat_g,
            e.match_confidence,
            e.raw_fragment,
            e.created_at
        FROM diary_log_entries e
        JOIN diary_logs l ON l.id = e.log_id
        WHERE l.log_date = ?
        ORDER BY e.created_at ASC, e.id ASC
        """,
        (day,),
    ).fetchall()

    entries = []
    for row in rows:
        kcal = row["energy_kcal"]
        entries.append(
            {
                "entry_id": int(row["entry_id"]),
                "log_id": int(row["log_id"]),
                "meal_tag": row["meal_tag"],
                "food_id": int(row["food_id"]),
                "food_name": row["food_name"],
                "amount": float(row["amount"]),
                "unit": row["unit"],
                "grams_equivalent": float(row["grams_equivalent"]),
                "energy_kcal": kcal,
                "protein_g": row["protein_g"],
                "carbs_g": row["carbs_g"],
                "fat_g": row["fat_g"],
                "match_confidence": row["match_confidence"],
                "raw_fragment": row["raw_fragment"],
                "logged_at": row["created_at"],
            }
        )

    nutrients = summarize_diary_nutrients(entries)
    totals = {
        **nutrients,
        "entry_count": len(entries),
        "targets": dict(PLACEHOLDER_DAILY_TARGETS),
        "remaining": remaining_budget(nutrients),
    }
    meals = group_entries_by_meal(entries)

    return {
        "log_date": day,
        "entries": entries,
        "meals": meals,
        "totals": totals,
    }
