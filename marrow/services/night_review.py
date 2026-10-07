"""Full-day night review aggregation (M7)."""

from __future__ import annotations

import sqlite3
from datetime import date
from typing import Any, Literal

from marrow.data.foods.nutrients import NUTRIENT_COLUMN_NAMES, NUTRIENT_FIELDS
from marrow.data.foods.units import scale_nutrients
from marrow.services.diary_log import list_diary_entries_for_date
from marrow.services.diary_totals import MACRO_KEYS, summarize_diary_nutrients
from marrow.services.food_repository import fetch_food_row, fetch_nutrients
from marrow.core.groq_settings import groq_configured
from marrow.services.groq_night_summary import maybe_groq_night_summary
from marrow.services.user_profile import (
    energy_status_for_day,
    fetch_micronutrient_targets,
    resolve_daily_macro_targets,
)

FlagKind = Literal["low", "high"]

# Nutrients where exceeding the target is the primary concern.
UPPER_LIMIT_NUTRIENTS: frozenset[str] = frozenset(
    {
        "sodium_mg",
        "saturated_fat_g",
        "trans_fat_g",
        "cholesterol_mg",
        "sugar_g",
        "alcohol_g",
    }
)

LOW_PCT_THRESHOLD = 0.70
HIGH_PCT_THRESHOLD = 1.20
TOP_CONTRIBUTOR_LIMIT = 3

NUTRIENT_LABELS: dict[str, str] = {
    "energy_kcal": "Calories",
    "protein_g": "Protein",
    "carbs_g": "Carbohydrates",
    "fat_g": "Fat",
    "fiber_g": "Fiber",
    "sugar_g": "Sugar",
    "saturated_fat_g": "Saturated fat",
    "trans_fat_g": "Trans fat",
    "monounsaturated_fat_g": "Monounsaturated fat",
    "polyunsaturated_fat_g": "Polyunsaturated fat",
    "cholesterol_mg": "Cholesterol",
    "sodium_mg": "Sodium",
    "potassium_mg": "Potassium",
    "calcium_mg": "Calcium",
    "iron_mg": "Iron",
    "magnesium_mg": "Magnesium",
    "phosphorus_mg": "Phosphorus",
    "zinc_mg": "Zinc",
    "copper_mg": "Copper",
    "manganese_mg": "Manganese",
    "selenium_ug": "Selenium",
    "vitamin_a_ug": "Vitamin A",
    "vitamin_c_mg": "Vitamin C",
    "vitamin_d_ug": "Vitamin D",
    "vitamin_e_mg": "Vitamin E",
    "vitamin_k_ug": "Vitamin K",
    "thiamin_mg": "Thiamin (B1)",
    "riboflavin_mg": "Riboflavin (B2)",
    "niacin_mg": "Niacin (B3)",
    "vitamin_b6_mg": "Vitamin B6",
    "folate_ug": "Folate",
    "vitamin_b12_ug": "Vitamin B12",
    "water_g": "Water",
    "alcohol_g": "Alcohol",
}


def _local_today() -> str:
    return date.today().isoformat()


def _nutrient_unit(key: str) -> str:
    for col, unit in NUTRIENT_FIELDS:
        if col == key:
            return unit
    return ""


def scale_entry_nutrients(
    conn: sqlite3.Connection,
    food_id: int,
    grams_equivalent: float,
) -> dict[str, float | None]:
    row = fetch_food_row(conn, food_id)
    if not row:
        return {key: None for key in NUTRIENT_COLUMN_NAMES}
    per_100 = fetch_nutrients(conn, food_id)
    return scale_nutrients(per_100, float(grams_equivalent), row["basis"])


def build_scaled_diary_entries(
    conn: sqlite3.Connection,
    diary_entries: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    scaled: list[dict[str, Any]] = []
    for entry in diary_entries:
        nutrients = scale_entry_nutrients(
            conn,
            int(entry["food_id"]),
            float(entry["grams_equivalent"]),
        )
        scaled.append(
            {
                "entry_id": entry.get("entry_id"),
                "food_id": entry["food_id"],
                "food_name": entry["food_name"],
                "meal_tag": entry.get("meal_tag"),
                "match_confidence": str(entry.get("match_confidence") or "ESTIMATED"),
                "energy_kcal": entry.get("energy_kcal"),
                "nutrients": nutrients,
            }
        )
    return scaled


def sum_nutrients_with_coverage(
    scaled_entries: list[dict[str, Any]],
) -> tuple[dict[str, float | None], dict[str, dict[str, int]]]:
    """Sum known values per nutrient; track how many entries lacked data."""
    totals: dict[str, float | None] = {key: None for key in NUTRIENT_COLUMN_NAMES}
    coverage: dict[str, dict[str, int]] = {
        key: {"with_data": 0, "missing": 0} for key in NUTRIENT_COLUMN_NAMES
    }
    if not scaled_entries:
        return totals, coverage

    for key in NUTRIENT_COLUMN_NAMES:
        partial = 0.0
        with_data = 0
        missing = 0
        for entry in scaled_entries:
            value = entry["nutrients"].get(key)
            if value is None:
                missing += 1
            else:
                with_data += 1
                partial += float(value)
        coverage[key] = {"with_data": with_data, "missing": missing}
        totals[key] = round(partial, 2) if with_data > 0 else None
    return totals, coverage


def top_contributors_per_nutrient(
    scaled_entries: list[dict[str, Any]],
    limit: int = TOP_CONTRIBUTOR_LIMIT,
) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = {}
    for key in NUTRIENT_COLUMN_NAMES:
        ranked: list[dict[str, Any]] = []
        for entry in scaled_entries:
            amount = entry["nutrients"].get(key)
            if amount is None or float(amount) <= 0:
                continue
            ranked.append(
                {
                    "food_name": entry["food_name"],
                    "food_id": entry["food_id"],
                    "entry_id": entry.get("entry_id"),
                    "amount": round(float(amount), 2),
                    "unit": _nutrient_unit(key),
                }
            )
        ranked.sort(key=lambda row: row["amount"], reverse=True)
        out[key] = ranked[:limit]
    return out


def macro_calorie_split(
    totals: dict[str, float | None],
) -> dict[str, float | None]:
    protein = totals.get("protein_g")
    carbs = totals.get("carbs_g")
    fat = totals.get("fat_g")
    if protein is None or carbs is None or fat is None:
        return {"protein_pct": None, "carbs_pct": None, "fat_pct": None}
    p_kcal = float(protein) * 4.0
    c_kcal = float(carbs) * 4.0
    f_kcal = float(fat) * 9.0
    macro_kcal = p_kcal + c_kcal + f_kcal
    if macro_kcal <= 0:
        return {"protein_pct": None, "carbs_pct": None, "fat_pct": None}
    return {
        "protein_pct": round(100.0 * p_kcal / macro_kcal, 1),
        "carbs_pct": round(100.0 * c_kcal / macro_kcal, 1),
        "fat_pct": round(100.0 * f_kcal / macro_kcal, 1),
    }


def estimated_calorie_share(
    diary_entries: list[dict[str, Any]],
) -> dict[str, float | None]:
    known_kcal = 0.0
    estimated_kcal = 0.0
    for entry in diary_entries:
        kcal = entry.get("energy_kcal")
        if kcal is None:
            continue
        kcal_f = float(kcal)
        known_kcal += kcal_f
        if str(entry.get("match_confidence") or "").upper() == "ESTIMATED":
            estimated_kcal += kcal_f
    if known_kcal <= 0:
        return {
            "estimated_kcal": round(estimated_kcal, 1),
            "known_kcal": None,
            "estimated_pct_of_known": None,
        }
    return {
        "estimated_kcal": round(estimated_kcal, 1),
        "known_kcal": round(known_kcal, 1),
        "estimated_pct_of_known": round(100.0 * estimated_kcal / known_kcal, 1),
    }


def _resolve_targets(
    conn: sqlite3.Connection,
    log_date: str,
) -> dict[str, dict[str, float | str]]:
    macro = resolve_daily_macro_targets(conn, log_date)
    micro = fetch_micronutrient_targets(conn)
    merged: dict[str, dict[str, float | str]] = {}
    for key in NUTRIENT_COLUMN_NAMES:
        unit = _nutrient_unit(key)
        if key in macro:
            merged[key] = {"target_value": float(macro[key]), "unit": unit}
        elif key in micro:
            merged[key] = {
                "target_value": float(micro[key]["target_value"]),
                "unit": str(micro[key].get("unit") or unit),
            }
    return merged


def _pct_of_target(consumed: float | None, target: float | None) -> float | None:
    if consumed is None or target is None or target <= 0:
        return None
    return consumed / float(target)


def flag_nutrient(
    key: str,
    consumed: float | None,
    target: float | None,
) -> FlagKind | None:
    if consumed is None or target is None or target <= 0:
        return None
    pct = float(consumed) / float(target)
    if key in UPPER_LIMIT_NUTRIENTS:
        if pct > HIGH_PCT_THRESHOLD:
            return "high"
        return None
    if pct < LOW_PCT_THRESHOLD:
        return "low"
    if pct > HIGH_PCT_THRESHOLD:
        return "high"
    return None


def build_nutrient_rows(
    totals: dict[str, float | None],
    coverage: dict[str, dict[str, int]],
    targets: dict[str, dict[str, float | str]],
    contributors: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key in NUTRIENT_COLUMN_NAMES:
        consumed = totals.get(key)
        target_info = targets.get(key)
        target_value = (
            float(target_info["target_value"]) if target_info else None
        )
        pct = _pct_of_target(consumed, target_value)
        flag = flag_nutrient(key, consumed, target_value)
        cov = coverage.get(key) or {"with_data": 0, "missing": 0}
        rows.append(
            {
                "key": key,
                "label": NUTRIENT_LABELS.get(key, key),
                "unit": _nutrient_unit(key),
                "consumed": consumed,
                "target": target_value,
                "pct_of_target": round(pct * 100.0, 1) if pct is not None else None,
                "status": "no_data" if consumed is None else "ok",
                "flag": flag,
                "coverage": cov,
                "partial_total": cov["missing"] > 0 and cov["with_data"] > 0,
                "top_contributors": contributors.get(key) or [],
            }
        )
    return rows


def build_rule_summary(
    energy_balance: dict[str, Any],
    nutrient_rows: list[dict[str, Any]],
    estimated: dict[str, float | None],
    entry_count: int,
) -> list[str]:
    lines: list[str] = []
    status = energy_balance.get("status")
    delta = energy_balance.get("energy_delta_kcal")
    if entry_count == 0:
        lines.append("No foods logged today — add meals to unlock a full night review.")
        return lines

    if status == "DEFICIT" and delta is not None:
        lines.append(
            f"You finished about {abs(int(round(delta)))} kcal under your calorie target."
        )
    elif status == "SURPLUS" and delta is not None:
        lines.append(
            f"You finished about {int(round(delta))} kcal above your calorie target."
        )
    elif status == "ON_TARGET":
        lines.append("Calories landed within your target band today.")

    lows = [r for r in nutrient_rows if r.get("flag") == "low"]
    highs = [r for r in nutrient_rows if r.get("flag") == "high"]
    if lows:
        names = ", ".join(
            f"{r['label']} ({r['pct_of_target']}% of target)" for r in lows[:4]
        )
        extra = " and others" if len(lows) > 4 else ""
        lines.append(f"Watch low intakes: {names}{extra}.")
    if highs:
        names = ", ".join(
            f"{r['label']} ({r['pct_of_target']}% of target)" for r in highs[:4]
        )
        extra = " and others" if len(highs) > 4 else ""
        lines.append(f"Elevated today: {names}{extra}.")

    est_pct = estimated.get("estimated_pct_of_known")
    if est_pct is not None and est_pct >= 40:
        lines.append(
            f"About {est_pct:.0f}% of logged calories used estimated food matches — "
            "micronutrient totals may shift if you refine portions."
        )

    partial = [r for r in nutrient_rows if r.get("partial_total")]
    if partial:
        lines.append(
            "Some nutrient totals only include foods with known data for that nutrient "
            "(missing values are shown as no data)."
        )

    if len(lines) == 1 and not lows and not highs:
        lines.append("Macro and micronutrient spread looks balanced against your targets.")

    return lines


def aggregate_night_review(
    scaled_entries: list[dict[str, Any]],
    diary_entries: list[dict[str, Any]],
    macro_totals: dict[str, float | None],
    targets: dict[str, dict[str, float | str]],
    energy_balance: dict[str, Any],
) -> dict[str, Any]:
    totals, coverage = sum_nutrients_with_coverage(scaled_entries)
    contributors = top_contributors_per_nutrient(scaled_entries)
    nutrient_rows = build_nutrient_rows(totals, coverage, targets, contributors)
    flagged = [row for row in nutrient_rows if row.get("flag")]
    estimated = estimated_calorie_share(diary_entries)
    macro_split = macro_calorie_split(totals)
    summary = build_rule_summary(
        energy_balance,
        nutrient_rows,
        estimated,
        len(diary_entries),
    )
    return {
        "nutrients": nutrient_rows,
        "flagged": flagged,
        "macro_split": macro_split,
        "estimated_confidence": estimated,
        "summary_lines": summary,
        "groq_summary": None,
    }


def get_night_review(
    conn: sqlite3.Connection,
    log_date: str | None = None,
) -> dict[str, Any]:
    day = log_date or _local_today()
    diary_day = list_diary_entries_for_date(conn, day)
    diary_entries = diary_day["entries"]
    scaled_entries = build_scaled_diary_entries(conn, diary_entries)
    macro_totals = summarize_diary_nutrients(diary_entries)
    targets = _resolve_targets(conn, day)
    energy_balance = energy_status_for_day(conn, macro_totals, day)
    review = aggregate_night_review(
        scaled_entries,
        diary_entries,
        macro_totals,
        targets,
        energy_balance,
    )
    if groq_configured() and review.get("groq_summary") is None:
        review["groq_summary"] = maybe_groq_night_summary(
            energy_balance,
            macro_totals,
            review.get("summary_lines") or [],
            review.get("flagged") or [],
        )
    return {
        "log_date": day,
        "entry_count": len(diary_entries),
        "energy_balance": energy_balance,
        "macro_totals": macro_totals,
        "targets": {
            key: targets[key]
            for key in MACRO_KEYS
            if key in targets
        },
        **review,
    }
