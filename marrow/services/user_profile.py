"""User profile, onboarding, and persisted daily targets (M6)."""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, date, datetime
from typing import Any

from marrow.services.diary_totals import PLACEHOLDER_DAILY_TARGETS
from marrow.services.energy_status import classify_energy_balance
from marrow.services.metabolism import (
    GYM_DAY_EXTRA_KCAL,
    MEDICAL_DISCLAIMER,
    compute_metabolic_plan,
    suggest_macro_targets,
)
from marrow.services.rda_defaults import default_micronutrient_targets

MACRO_KEYS = ("energy_kcal", "protein_g", "carbs_g", "fat_g")
DAY_KINDS = ("default", "gym", "rest")


def _row_to_profile(row: sqlite3.Row | None) -> dict[str, Any]:
    if not row:
        return {"onboarding_completed": False}
    gym_weekdays = None
    raw_gym = row["gym_weekdays"]
    if raw_gym:
        try:
            gym_weekdays = json.loads(raw_gym)
        except json.JSONDecodeError:
            gym_weekdays = None
    return {
        "display_name": row["display_name"],
        "age_years": row["age_years"],
        "sex": row["sex"],
        "height_cm": row["height_cm"],
        "weight_kg": row["weight_kg"],
        "activity_level": row["activity_level"],
        "goal": row["goal"],
        "calorie_tolerance_pct": float(row["calorie_tolerance_pct"] or 5.0),
        "use_split_day_targets": bool(row["use_split_day_targets"]),
        "gym_weekdays": gym_weekdays,
        "disclaimer_acknowledged_at": row["disclaimer_acknowledged_at"],
        "onboarding_completed_at": row["onboarding_completed_at"],
        "onboarding_completed": bool(row["onboarding_completed_at"]),
        "disclaimer": MEDICAL_DISCLAIMER,
    }


def get_user_profile(conn: sqlite3.Connection) -> dict[str, Any]:
    row = conn.execute("SELECT * FROM user_profile WHERE id = 1").fetchone()
    profile = _row_to_profile(row)
    profile["macro_targets"] = fetch_macro_targets(conn)
    profile["micronutrient_targets"] = fetch_micronutrient_targets(conn)
    return profile


def fetch_macro_targets(conn: sqlite3.Connection) -> dict[str, dict[str, float]]:
    rows = conn.execute(
        "SELECT day_kind, energy_kcal, protein_g, carbs_g, fat_g FROM daily_macro_targets"
    ).fetchall()
    out: dict[str, dict[str, float]] = {}
    for row in rows:
        out[row["day_kind"]] = {
            "energy_kcal": float(row["energy_kcal"]),
            "protein_g": float(row["protein_g"]),
            "carbs_g": float(row["carbs_g"]),
            "fat_g": float(row["fat_g"]),
        }
    return out


def fetch_micronutrient_targets(conn: sqlite3.Connection) -> dict[str, dict]:
    rows = conn.execute(
        "SELECT nutrient_key, target_value, unit FROM micronutrient_targets"
    ).fetchall()
    return {
        row["nutrient_key"]: {
            "target_value": float(row["target_value"]),
            "unit": row["unit"],
        }
        for row in rows
    }


def preview_metabolic_plan(payload: dict) -> dict:
    return compute_metabolic_plan(
        age_years=int(payload["age_years"]),
        sex=str(payload["sex"]),
        height_cm=float(payload["height_cm"]),
        weight_kg=float(payload["weight_kg"]),
        activity_level=str(payload["activity_level"]),
        goal=str(payload["goal"]),
    )


def _validate_onboarding(payload: dict) -> dict:
    required = (
        "age_years",
        "sex",
        "height_cm",
        "weight_kg",
        "activity_level",
        "goal",
    )
    for key in required:
        if payload.get(key) is None:
            raise ValueError(f"missing required field: {key}")
    if not payload.get("disclaimer_acknowledged"):
        raise ValueError("disclaimer must be acknowledged")
    age = int(payload["age_years"])
    if age < 13 or age > 100:
        raise ValueError("age_years must be between 13 and 100")
    height = float(payload["height_cm"])
    weight = float(payload["weight_kg"])
    if height < 100 or height > 250:
        raise ValueError("height_cm out of range")
    if weight < 30 or weight > 300:
        raise ValueError("weight_kg out of range")
    return payload


def _upsert_macro_targets(conn: sqlite3.Connection, day_kind: str, macros: dict) -> None:
    conn.execute(
        """
        INSERT INTO daily_macro_targets (day_kind, energy_kcal, protein_g, carbs_g, fat_g, updated_at)
        VALUES (?, ?, ?, ?, ?, datetime('now'))
        ON CONFLICT(day_kind) DO UPDATE SET
            energy_kcal = excluded.energy_kcal,
            protein_g = excluded.protein_g,
            carbs_g = excluded.carbs_g,
            fat_g = excluded.fat_g,
            updated_at = datetime('now')
        """,
        (
            day_kind,
            float(macros["energy_kcal"]),
            float(macros["protein_g"]),
            float(macros["carbs_g"]),
            float(macros["fat_g"]),
        ),
    )


def _seed_micronutrient_defaults(conn: sqlite3.Connection, sex: str) -> None:
    defaults = default_micronutrient_targets(sex)
    for key, item in defaults.items():
        conn.execute(
            """
            INSERT INTO micronutrient_targets (nutrient_key, target_value, unit, updated_at)
            VALUES (?, ?, ?, datetime('now'))
            ON CONFLICT(nutrient_key) DO NOTHING
            """,
            (key, item["target_value"], item["unit"]),
        )


def quick_start_tracking(conn: sqlite3.Connection) -> dict:
    """Skip demographics wizard — use neutral defaults and start meal logging."""
    now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")
    conn.execute(
        """
        UPDATE user_profile SET
            goal = 'maintain',
            activity_level = 'moderate',
            calorie_tolerance_pct = 5.0,
            use_split_day_targets = 0,
            gym_weekdays = NULL,
            disclaimer_acknowledged_at = ?,
            onboarding_completed_at = ?,
            updated_at = datetime('now')
        WHERE id = 1
        """,
        (now, now),
    )

    default = dict(PLACEHOLDER_DAILY_TARGETS)
    gym_energy = float(default["energy_kcal"]) + GYM_DAY_EXTRA_KCAL
    gym = suggest_macro_targets(gym_energy, weight_kg=70.0, goal="maintain")

    _upsert_macro_targets(conn, "default", default)
    _upsert_macro_targets(conn, "gym", gym)
    _upsert_macro_targets(conn, "rest", default)
    _seed_micronutrient_defaults(conn, "male")

    conn.commit()
    return get_user_profile(conn)


def complete_onboarding(conn: sqlite3.Connection, payload: dict) -> dict:
    _validate_onboarding(payload)
    sex = str(payload["sex"])
    plan = preview_metabolic_plan(payload)

    macro_targets = payload.get("macro_targets") or {}
    default_macros = macro_targets.get("default") or plan["suggested_default"]
    gym_macros = macro_targets.get("gym") or plan["suggested_gym"]
    rest_macros = macro_targets.get("rest") or plan["suggested_rest"]

    use_split = bool(payload.get("use_split_day_targets"))
    gym_weekdays = payload.get("gym_weekdays")
    gym_json = json.dumps(gym_weekdays) if gym_weekdays is not None else None

    tolerance = float(payload.get("calorie_tolerance_pct") or 5.0)
    if tolerance < 1 or tolerance > 25:
        raise ValueError("calorie_tolerance_pct must be between 1 and 25")

    now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")
    conn.execute(
        """
        UPDATE user_profile SET
            age_years = ?,
            sex = ?,
            height_cm = ?,
            weight_kg = ?,
            activity_level = ?,
            goal = ?,
            calorie_tolerance_pct = ?,
            use_split_day_targets = ?,
            gym_weekdays = ?,
            disclaimer_acknowledged_at = ?,
            onboarding_completed_at = ?,
            updated_at = datetime('now')
        WHERE id = 1
        """,
        (
            int(payload["age_years"]),
            sex,
            float(payload["height_cm"]),
            float(payload["weight_kg"]),
            str(payload["activity_level"]),
            str(payload["goal"]),
            tolerance,
            1 if use_split else 0,
            gym_json,
            now,
            now,
        ),
    )

    _upsert_macro_targets(conn, "default", default_macros)
    _upsert_macro_targets(conn, "gym", gym_macros)
    _upsert_macro_targets(conn, "rest", rest_macros)

    micro_overrides = payload.get("micronutrient_targets")
    if micro_overrides:
        for key, item in micro_overrides.items():
            conn.execute(
                """
                INSERT INTO micronutrient_targets (nutrient_key, target_value, unit, updated_at)
                VALUES (?, ?, ?, datetime('now'))
                ON CONFLICT(nutrient_key) DO UPDATE SET
                    target_value = excluded.target_value,
                    unit = excluded.unit,
                    updated_at = datetime('now')
                """,
                (key, float(item["target_value"]), str(item["unit"])),
            )
    else:
        _seed_micronutrient_defaults(conn, sex)

    conn.execute(
        """
        INSERT INTO weight_log (logged_date, weight_kg, note)
        VALUES (?, ?, ?)
        """,
        (date.today().isoformat(), float(payload["weight_kg"]), "onboarding"),
    )

    conn.commit()
    profile = get_user_profile(conn)
    profile["plan"] = plan
    return profile


def update_macro_targets(conn: sqlite3.Connection, payload: dict) -> dict:
    row = conn.execute(
        "SELECT onboarding_completed_at FROM user_profile WHERE id = 1"
    ).fetchone()
    if not row or not row["onboarding_completed_at"]:
        raise ValueError("complete onboarding first")

    for day_kind in DAY_KINDS:
        macros = payload.get(day_kind)
        if macros:
            _upsert_macro_targets(conn, day_kind, macros)

    if "calorie_tolerance_pct" in payload:
        tol = float(payload["calorie_tolerance_pct"])
        if tol < 1 or tol > 25:
            raise ValueError("calorie_tolerance_pct must be between 1 and 25")
        conn.execute(
            "UPDATE user_profile SET calorie_tolerance_pct = ?, updated_at = datetime('now') WHERE id = 1",
            (tol,),
        )

    conn.commit()
    return get_user_profile(conn)


def _weekday_for_iso(log_date: str) -> int:
    return date.fromisoformat(log_date).weekday()


def resolve_day_kind(conn: sqlite3.Connection, log_date: str) -> str:
    row = conn.execute(
        """
        SELECT use_split_day_targets, gym_weekdays
        FROM user_profile WHERE id = 1
        """
    ).fetchone()
    if not row or not row["use_split_day_targets"]:
        return "default"
    try:
        gym_days = json.loads(row["gym_weekdays"] or "[]")
    except json.JSONDecodeError:
        gym_days = []
    if not isinstance(gym_days, list):
        gym_days = []
    weekday = _weekday_for_iso(log_date)
    return "gym" if weekday in gym_days else "rest"


def resolve_daily_macro_targets(
    conn: sqlite3.Connection,
    log_date: str | None = None,
) -> dict[str, float]:
    day = log_date or date.today().isoformat()
    profile = conn.execute(
        "SELECT onboarding_completed_at FROM user_profile WHERE id = 1"
    ).fetchone()
    if not profile or not profile["onboarding_completed_at"]:
        from marrow.services.diary_totals import PLACEHOLDER_DAILY_TARGETS

        return dict(PLACEHOLDER_DAILY_TARGETS)

    kind = resolve_day_kind(conn, day)
    row = conn.execute(
        """
        SELECT energy_kcal, protein_g, carbs_g, fat_g
        FROM daily_macro_targets WHERE day_kind = ?
        """,
        (kind,),
    ).fetchone()
    if not row:
        row = conn.execute(
            """
            SELECT energy_kcal, protein_g, carbs_g, fat_g
            FROM daily_macro_targets WHERE day_kind = 'default'
            """
        ).fetchone()
    if not row:
        from marrow.services.diary_totals import PLACEHOLDER_DAILY_TARGETS

        return dict(PLACEHOLDER_DAILY_TARGETS)

    return {
        "energy_kcal": float(row["energy_kcal"]),
        "protein_g": float(row["protein_g"]),
        "carbs_g": float(row["carbs_g"]),
        "fat_g": float(row["fat_g"]),
    }


def energy_status_for_day(
    conn: sqlite3.Connection,
    consumed: dict[str, float | None],
    log_date: str | None = None,
) -> dict:
    targets = resolve_daily_macro_targets(conn, log_date)
    row = conn.execute(
        "SELECT calorie_tolerance_pct FROM user_profile WHERE id = 1"
    ).fetchone()
    tolerance = float(row["calorie_tolerance_pct"]) if row else 5.0
    status = classify_energy_balance(
        consumed.get("energy_kcal"),
        targets["energy_kcal"],
        tolerance_pct=tolerance,
    )
    status["target_day_kind"] = resolve_day_kind(
        conn, log_date or date.today().isoformat()
    )
    return status
