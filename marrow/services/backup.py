"""Local rotating backups and manual export/import (JSON + diary CSV)."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import shutil
import sqlite3
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Literal

from marrow.core.paths import backups_dir, database_path
from marrow.data.foods.nutrients import NUTRIENT_COLUMN_NAMES
from marrow.services.food_search import search_foods

BACKUP_FORMAT = "marrow-backup"
BACKUP_VERSION = 1
MAX_ROTATING_BACKUPS = 7
AUTO_STAMP_NAME = ".last_auto_backup_date"

DIARY_CSV_COLUMNS = [
    "log_date",
    "meal_tag",
    "food_name",
    "amount",
    "unit",
    "grams_equivalent",
    "energy_kcal",
    "protein_g",
    "carbs_g",
    "fat_g",
    "match_confidence",
    "source_text",
]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _backup_filename() -> str:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"marrow-{stamp}.db"


def list_backups() -> list[dict[str, Any]]:
    root = backups_dir()
    rows: list[dict[str, Any]] = []
    for path in sorted(root.glob("marrow-*.db"), reverse=True):
        stat = path.stat()
        rows.append(
            {
                "filename": path.name,
                "path": str(path),
                "size_bytes": int(stat.st_size),
                "modified_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
            }
        )
    return rows


def _prune_rotating_backups() -> int:
    files = sorted(backups_dir().glob("marrow-*.db"), key=lambda p: p.stat().st_mtime, reverse=True)
    removed = 0
    for extra in files[MAX_ROTATING_BACKUPS:]:
        extra.unlink(missing_ok=True)
        removed += 1
    return removed


def create_backup_file() -> dict[str, Any]:
    """Copy the live user database into the rotating backups folder."""
    src = database_path()
    if not src.exists():
        raise FileNotFoundError("Database does not exist yet")
    dest = backups_dir() / _backup_filename()
    shutil.copy2(src, dest)
    _prune_rotating_backups()
    stat = dest.stat()
    return {
        "filename": dest.name,
        "path": str(dest),
        "size_bytes": int(stat.st_size),
        "modified_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
    }


def maybe_automatic_backup() -> dict[str, Any] | None:
    """At most one automatic file backup per local calendar day."""
    db = database_path()
    if not db.exists():
        return None
    stamp_path = backups_dir() / AUTO_STAMP_NAME
    today = date.today().isoformat()
    if stamp_path.exists() and stamp_path.read_text(encoding="utf-8").strip() == today:
        return None
    info = create_backup_file()
    stamp_path.write_text(today, encoding="utf-8")
    return info


def restore_backup_file(filename: str) -> dict[str, Any]:
    safe = Path(filename).name
    if safe != filename or ".." in safe:
        raise ValueError("Invalid backup filename")
    src = backups_dir() / safe
    if not src.is_file():
        raise FileNotFoundError(f"Backup not found: {safe}")
    dest = database_path()
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        pre = backups_dir() / f"pre-restore-{datetime.now().strftime('%Y%m%d-%H%M%S')}.db"
        shutil.copy2(dest, pre)
    shutil.copy2(src, dest)
    return {"restored_from": safe, "database_path": str(dest)}


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {k: row[k] for k in row.keys()}


def export_user_json(conn: sqlite3.Connection) -> dict[str, Any]:
    profile = conn.execute("SELECT * FROM user_profile WHERE id = 1").fetchone()
    macros = conn.execute("SELECT * FROM daily_macro_targets").fetchall()
    micros = conn.execute("SELECT * FROM micronutrient_targets").fetchall()
    weights = conn.execute("SELECT * FROM weight_log ORDER BY logged_date, id").fetchall()
    logs = conn.execute("SELECT * FROM diary_logs ORDER BY log_date, id").fetchall()
    log_ids = [int(r["id"]) for r in logs]
    entries: list[dict[str, Any]] = []
    if log_ids:
        placeholders = ", ".join("?" for _ in log_ids)
        entry_rows = conn.execute(
            f"SELECT * FROM diary_log_entries WHERE log_id IN ({placeholders}) ORDER BY log_id, position",
            log_ids,
        ).fetchall()
        entries = [_row_to_dict(r) for r in entry_rows]

    custom_foods = conn.execute("SELECT * FROM foods WHERE source = 'custom'").fetchall()
    custom_ids = [int(r["id"]) for r in custom_foods]
    nutrients: list[dict[str, Any]] = []
    servings: list[dict[str, Any]] = []
    if custom_ids:
        ph = ", ".join("?" for _ in custom_ids)
        nutrients = [
            _row_to_dict(r)
            for r in conn.execute(
                f"SELECT * FROM food_nutrients WHERE food_id IN ({ph})",
                custom_ids,
            ).fetchall()
        ]
        servings = [
            _row_to_dict(r)
            for r in conn.execute(
                f"SELECT * FROM food_servings WHERE food_id IN ({ph})",
                custom_ids,
            ).fetchall()
        ]

    recipes = conn.execute("SELECT * FROM recipes").fetchall()
    recipe_ids = [int(r["id"]) for r in recipes]
    recipe_ingredients: list[dict[str, Any]] = []
    if recipe_ids:
        ph = ", ".join("?" for _ in recipe_ids)
        recipe_ingredients = [
            _row_to_dict(r)
            for r in conn.execute(
                f"SELECT * FROM recipe_ingredients WHERE recipe_id IN ({ph})",
                recipe_ids,
            ).fetchall()
        ]

    return {
        "format": BACKUP_FORMAT,
        "version": BACKUP_VERSION,
        "exported_at": _utc_now_iso(),
        "checksum": "",
        "user_profile": _row_to_dict(profile) if profile else None,
        "daily_macro_targets": [_row_to_dict(r) for r in macros],
        "micronutrient_targets": [_row_to_dict(r) for r in micros],
        "weight_log": [_row_to_dict(r) for r in weights],
        "diary_logs": [_row_to_dict(r) for r in logs],
        "diary_log_entries": entries,
        "custom_foods": [_row_to_dict(r) for r in custom_foods],
        "food_nutrients_custom": nutrients,
        "food_servings_custom": servings,
        "recipes": [_row_to_dict(r) for r in recipes],
        "recipe_ingredients": recipe_ingredients,
    }


def _attach_checksum(payload: dict[str, Any]) -> dict[str, Any]:
    body = {k: v for k, v in payload.items() if k != "checksum"}
    digest = hashlib.sha256(json.dumps(body, sort_keys=True).encode("utf-8")).hexdigest()
    payload["checksum"] = digest
    return payload


def export_user_json_text(conn: sqlite3.Connection) -> str:
    payload = _attach_checksum(export_user_json(conn))
    return json.dumps(payload, indent=2)


def export_diary_csv_text(conn: sqlite3.Connection) -> str:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=DIARY_CSV_COLUMNS, extrasaction="ignore")
    writer.writeheader()
    rows = conn.execute(
        """
        SELECT
            l.log_date,
            l.meal_tag,
            l.source_text,
            e.food_name,
            e.amount,
            e.unit,
            e.grams_equivalent,
            e.energy_kcal,
            e.protein_g,
            e.carbs_g,
            e.fat_g,
            e.match_confidence
        FROM diary_log_entries e
        JOIN diary_logs l ON l.id = e.log_id
        ORDER BY l.log_date, l.id, e.position
        """
    ).fetchall()
    for row in rows:
        writer.writerow({col: row[col] for col in DIARY_CSV_COLUMNS})
    return buf.getvalue()


def _validate_import_payload(data: dict[str, Any]) -> None:
    if data.get("format") != BACKUP_FORMAT:
        raise ValueError("Unrecognized backup format")
    version = int(data.get("version", 0))
    if version != BACKUP_VERSION:
        raise ValueError(f"Unsupported backup version: {version}")
    checksum = data.get("checksum")
    if checksum:
        body = {k: v for k, v in data.items() if k != "checksum"}
        expected = hashlib.sha256(json.dumps(body, sort_keys=True).encode("utf-8")).hexdigest()
        if checksum != expected:
            raise ValueError("Backup checksum mismatch")


def import_user_json(conn: sqlite3.Connection, data: dict[str, Any], *, mode: Literal["replace"] = "replace") -> dict[str, int]:
    _validate_import_payload(data)
    if mode != "replace":
        raise ValueError("Only replace mode is supported")

    conn.execute("DELETE FROM diary_log_entries")
    conn.execute("DELETE FROM diary_logs")
    conn.execute("DELETE FROM weight_log")
    conn.execute("DELETE FROM recipe_ingredients")
    conn.execute("DELETE FROM recipes")
    conn.execute("DELETE FROM food_servings WHERE food_id IN (SELECT id FROM foods WHERE source = 'custom')")
    conn.execute("DELETE FROM food_nutrients WHERE food_id IN (SELECT id FROM foods WHERE source = 'custom')")
    conn.execute("DELETE FROM foods WHERE source = 'custom'")

    profile = data.get("user_profile")
    if isinstance(profile, dict):
        cols = [k for k in profile.keys() if k != "id"]
        if cols:
            assignments = ", ".join(f"{c} = ?" for c in cols)
            conn.execute(
                f"UPDATE user_profile SET {assignments} WHERE id = 1",
                [profile[c] for c in cols],
            )

    for row in data.get("daily_macro_targets") or []:
        if not isinstance(row, dict):
            continue
        conn.execute(
            """
            INSERT INTO daily_macro_targets (day_kind, energy_kcal, protein_g, carbs_g, fat_g, updated_at)
            VALUES (?, ?, ?, ?, ?, COALESCE(?, datetime('now')))
            ON CONFLICT (day_kind) DO UPDATE SET
                energy_kcal = excluded.energy_kcal,
                protein_g = excluded.protein_g,
                carbs_g = excluded.carbs_g,
                fat_g = excluded.fat_g,
                updated_at = excluded.updated_at
            """,
            (
                row.get("day_kind"),
                row.get("energy_kcal"),
                row.get("protein_g"),
                row.get("carbs_g"),
                row.get("fat_g"),
                row.get("updated_at"),
            ),
        )

    for row in data.get("micronutrient_targets") or []:
        if not isinstance(row, dict):
            continue
        conn.execute(
            """
            INSERT INTO micronutrient_targets (nutrient_key, target_value, unit, updated_at)
            VALUES (?, ?, ?, COALESCE(?, datetime('now')))
            ON CONFLICT (nutrient_key) DO UPDATE SET
                target_value = excluded.target_value,
                unit = excluded.unit,
                updated_at = excluded.updated_at
            """,
            (row.get("nutrient_key"), row.get("target_value"), row.get("unit"), row.get("updated_at")),
        )

    for row in data.get("weight_log") or []:
        if not isinstance(row, dict):
            continue
        conn.execute(
            """
            INSERT INTO weight_log (logged_date, weight_kg, note, created_at)
            VALUES (?, ?, ?, COALESCE(?, datetime('now')))
            """,
            (row.get("logged_date"), row.get("weight_kg"), row.get("note"), row.get("created_at")),
        )

    food_id_map: dict[int, int] = {}
    for row in data.get("custom_foods") or []:
        if not isinstance(row, dict):
            continue
        old_id = int(row["id"])
        cur = conn.execute(
            """
            INSERT INTO foods (
                source, source_food_id, name, name_normalized, basis,
                preparation, data_quality, brand, barcode, locale
            ) VALUES ('custom', ?, ?, ?, ?, ?, ?, ?, ?, ?)
            RETURNING id
            """,
            (
                row.get("source_food_id") or f"import-{old_id}",
                row.get("name"),
                row.get("name_normalized") or str(row.get("name", "")).lower(),
                row.get("basis") or "per_100g",
                row.get("preparation") or "unknown",
                row.get("data_quality") or "estimated",
                row.get("brand"),
                row.get("barcode"),
                row.get("locale"),
            ),
        )
        food_id_map[old_id] = int(cur.fetchone()[0])

    nutrient_cols = ", ".join(NUTRIENT_COLUMN_NAMES)
    for row in data.get("food_nutrients_custom") or []:
        if not isinstance(row, dict):
            continue
        old_food = int(row["food_id"])
        new_food = food_id_map.get(old_food)
        if not new_food:
            continue
        conn.execute(
            f"""
            INSERT INTO food_nutrients (food_id, {nutrient_cols})
            VALUES (?, {", ".join("?" for _ in NUTRIENT_COLUMN_NAMES)})
            """,
            (new_food, *[row.get(c) for c in NUTRIENT_COLUMN_NAMES]),
        )

    for row in data.get("food_servings_custom") or []:
        if not isinstance(row, dict):
            continue
        old_food = int(row["food_id"])
        new_food = food_id_map.get(old_food)
        if not new_food:
            continue
        conn.execute(
            """
            INSERT INTO food_servings (
                food_id, label, amount, unit, grams_equivalent, is_default, sort_order
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                new_food,
                row.get("label"),
                row.get("amount"),
                row.get("unit"),
                row.get("grams_equivalent"),
                row.get("is_default"),
                row.get("sort_order"),
            ),
        )

    recipe_id_map: dict[int, int] = {}
    for row in data.get("recipes") or []:
        if not isinstance(row, dict):
            continue
        old_id = int(row["id"])
        cur = conn.execute(
            """
            INSERT INTO recipes (name, servings_count, notes, created_at, updated_at)
            VALUES (?, ?, ?, COALESCE(?, datetime('now')), COALESCE(?, datetime('now')))
            RETURNING id
            """,
            (row.get("name"), row.get("servings_count"), row.get("notes"), row.get("created_at"), row.get("updated_at")),
        )
        recipe_id_map[old_id] = int(cur.fetchone()[0])

    for row in data.get("recipe_ingredients") or []:
        if not isinstance(row, dict):
            continue
        recipe_id = recipe_id_map.get(int(row["recipe_id"]))
        if not recipe_id or row.get("food_id") is None:
            continue
        old_food = int(row["food_id"])
        food_id = food_id_map.get(old_food, old_food)
        conn.execute(
            """
            INSERT INTO recipe_ingredients (recipe_id, food_id, amount, unit, grams_equivalent, sort_order)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                recipe_id,
                food_id,
                row.get("amount"),
                row.get("unit"),
                row.get("grams_equivalent"),
                row.get("sort_order"),
            ),
        )

    log_id_map: dict[int, int] = {}
    for row in data.get("diary_logs") or []:
        if not isinstance(row, dict):
            continue
        old_id = int(row["id"])
        cur = conn.execute(
            """
            INSERT INTO diary_logs (log_date, meal_tag, created_at, source_text, notes)
            VALUES (?, ?, COALESCE(?, datetime('now')), ?, ?)
            RETURNING id
            """,
            (row.get("log_date"), row.get("meal_tag"), row.get("created_at"), row.get("source_text"), row.get("notes")),
        )
        log_id_map[old_id] = int(cur.fetchone()[0])

    entry_count = 0
    for row in data.get("diary_log_entries") or []:
        if not isinstance(row, dict):
            continue
        log_id = log_id_map.get(int(row["log_id"]))
        food_id = int(row["food_id"])
        if not log_id:
            continue
        conn.execute(
            """
            INSERT INTO diary_log_entries (
                log_id, food_id, food_name, amount, unit, grams_equivalent,
                energy_kcal, protein_g, carbs_g, fat_g, match_confidence,
                raw_fragment, position, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, COALESCE(?, datetime('now')))
            """,
            (
                log_id,
                food_id,
                row.get("food_name"),
                row.get("amount"),
                row.get("unit"),
                row.get("grams_equivalent"),
                row.get("energy_kcal"),
                row.get("protein_g"),
                row.get("carbs_g"),
                row.get("fat_g"),
                row.get("match_confidence"),
                row.get("raw_fragment"),
                row.get("position"),
                row.get("created_at"),
            ),
        )
        entry_count += 1

    conn.commit()
    return {
        "diary_logs": len(log_id_map),
        "diary_entries": entry_count,
        "weight_entries": len(data.get("weight_log") or []),
        "custom_foods": len(food_id_map),
    }


def import_diary_csv(conn: sqlite3.Connection, csv_text: str) -> dict[str, int]:
    reader = csv.DictReader(io.StringIO(csv_text))
    if not reader.fieldnames:
        raise ValueError("CSV is empty")
    missing = [c for c in DIARY_CSV_COLUMNS if c not in reader.fieldnames]
    if missing:
        raise ValueError(f"CSV missing columns: {', '.join(missing)}")

    logs_created = 0
    entries_created = 0
    log_cache: dict[tuple[str, str], int] = {}

    for row in reader:
        log_date = (row.get("log_date") or "").strip()
        meal_tag = (row.get("meal_tag") or "snack").strip().lower()
        if not log_date:
            continue
        key = (log_date, meal_tag)
        log_id = log_cache.get(key)
        if not log_id:
            cur = conn.execute(
                """
                INSERT INTO diary_logs (log_date, meal_tag, source_text)
                VALUES (?, ?, ?)
                RETURNING id
                """,
                (log_date, meal_tag, row.get("source_text")),
            )
            log_id = int(cur.fetchone()[0])
            log_cache[key] = log_id
            logs_created += 1

        food_name = (row.get("food_name") or "").strip()
        if not food_name:
            continue
        search = search_foods(conn, food_name, limit=1)
        hit = (search.get("results") or [None])[0]
        if not hit:
            continue
        food_id = int(hit["id"])
        try:
            amount = float(row.get("amount") or 1)
        except (TypeError, ValueError):
            amount = 1.0
        unit = (row.get("unit") or "serving").strip() or "serving"
        try:
            grams = float(row.get("grams_equivalent") or hit.get("grams_equivalent") or 100)
        except (TypeError, ValueError):
            grams = 100.0

        def _opt_float(key: str) -> float | None:
            raw = row.get(key)
            if raw is None or str(raw).strip() == "":
                return None
            try:
                return float(raw)
            except (TypeError, ValueError):
                return None

        conn.execute(
            """
            INSERT INTO diary_log_entries (
                log_id, food_id, food_name, amount, unit, grams_equivalent,
                energy_kcal, protein_g, carbs_g, fat_g, match_confidence, position
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                log_id,
                food_id,
                food_name,
                amount,
                unit,
                grams,
                _opt_float("energy_kcal"),
                _opt_float("protein_g"),
                _opt_float("carbs_g"),
                _opt_float("fat_g"),
                (row.get("match_confidence") or "ESTIMATED").strip().upper(),
                entries_created,
            ),
        )
        entries_created += 1

    conn.commit()
    return {"diary_logs": logs_created, "diary_entries": entries_created}
