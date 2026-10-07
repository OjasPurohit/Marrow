"""Trend series: macros, balance, micronutrients, weight (M9)."""

from __future__ import annotations

import sqlite3
from collections import defaultdict
from datetime import date, timedelta
from typing import Any

from marrow.services.diary_history import _entries_by_date, _summarize_day
from marrow.services.night_review import (
    build_scaled_diary_entries,
    sum_nutrients_with_coverage,
)
from marrow.services.diary_log import list_diary_entries_for_date
from marrow.services.weight_log import list_weight_entries, smooth_weight_trend

ALLOWED_RANGES = (7, 30, 90)
DEFAULT_MICRO_KEYS = ("fiber_g", "iron_mg", "vitamin_d_ug")


def _local_today() -> str:
    return date.today().isoformat()


def _rolling_mean(values: list[float | None], window: int = 7) -> list[float | None]:
    out: list[float | None] = []
    for idx in range(len(values)):
        slice_start = max(0, idx - window + 1)
        chunk = [v for v in values[slice_start : idx + 1] if v is not None]
        if not chunk:
            out.append(None)
        else:
            out.append(round(sum(chunk) / len(chunk), 1))
    return out


def _iso_week_start(day: date) -> date:
    return day - timedelta(days=day.weekday())


def _weekly_balance_rows(
    days: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for day in days:
        if not day["logged"]:
            continue
        week_start = _iso_week_start(date.fromisoformat(day["log_date"])).isoformat()
        buckets[week_start].append(day)

    rows: list[dict[str, Any]] = []
    cumulative = 0.0
    for week_start in sorted(buckets.keys()):
        bucket = buckets[week_start]
        deltas = [d["energy_delta_kcal"] for d in bucket if d["energy_delta_kcal"] is not None]
        avg_delta = round(sum(deltas) / len(deltas), 1) if deltas else None
        if avg_delta is not None:
            cumulative = round(cumulative + avg_delta, 1)
        rows.append(
            {
                "week_start": week_start,
                "days_logged": len(bucket),
                "avg_energy_delta_kcal": avg_delta,
                "cumulative_balance_kcal": cumulative if avg_delta is not None else None,
            }
        )
    return rows


def _micro_series_for_day(
    conn: sqlite3.Connection,
    log_date: str,
    keys: tuple[str, ...],
) -> dict[str, float | None]:
    diary = list_diary_entries_for_date(conn, log_date)
    if not diary["entries"]:
        return {key: None for key in keys}
    scaled = build_scaled_diary_entries(conn, diary["entries"])
    totals, _coverage = sum_nutrients_with_coverage(scaled)
    return {key: totals.get(key) for key in keys}


def get_trend_series(
    conn: sqlite3.Connection,
    range_days: int = 30,
    micronutrient_keys: list[str] | None = None,
    end_date: str | None = None,
) -> dict[str, Any]:
    if range_days not in ALLOWED_RANGES:
        raise ValueError(f"range_days must be one of {ALLOWED_RANGES}")

    end = date.fromisoformat(end_date or _local_today())
    start = end - timedelta(days=range_days - 1)
    grouped = _entries_by_date(conn, start.isoformat(), end.isoformat())

    micro_keys = tuple(micronutrient_keys or DEFAULT_MICRO_KEYS)
    days: list[dict[str, Any]] = []
    cursor = start
    while cursor <= end:
        iso = cursor.isoformat()
        days.append(_summarize_day(conn, iso, grouped.get(iso, [])))
        cursor += timedelta(days=1)

    dates = [d["log_date"] for d in days]
    energy = [d["energy_kcal"] for d in days]
    protein = [d["protein_g"] for d in days]
    deltas = [d["energy_delta_kcal"] for d in days]

    rolling_energy = _rolling_mean([float(v) if v is not None else None for v in energy])
    rolling_balance = _rolling_mean([float(v) if v is not None else None for v in deltas])

    micro_series: dict[str, list[float | None]] = {key: [] for key in micro_keys}
    for day in days:
        if not day["logged"]:
            for key in micro_keys:
                micro_series[key].append(None)
            continue
        row = _micro_series_for_day(conn, day["log_date"], micro_keys)
        for key in micro_keys:
            micro_series[key].append(row.get(key))

    weights = list_weight_entries(conn, limit=max(range_days * 2, 120))
    weight_by_date: dict[str, float] = {}
    for entry in sorted(weights, key=lambda r: (r["logged_date"], r["id"])):
        weight_by_date[entry["logged_date"]] = float(entry["weight_kg"])

    weight_points = [weight_by_date.get(d) for d in dates]
    smooth = smooth_weight_trend(
        [{"logged_date": d, "weight_kg": weight_by_date.get(d)} for d in dates],
        window=7,
    )

    weekly_avg_balance = _weekly_balance_rows(days)

    return {
        "range_days": range_days,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "dates": dates,
        "energy_kcal": energy,
        "protein_g": protein,
        "energy_delta_kcal": deltas,
        "rolling_7_energy_kcal": rolling_energy,
        "rolling_7_balance_kcal": rolling_balance,
        "micronutrients": micro_series,
        "micronutrient_keys": list(micro_keys),
        "weight_kg": weight_points,
        "weight_smooth_kg": smooth,
        "weekly_balance": weekly_avg_balance,
        "days_logged": sum(1 for d in days if d["logged"]),
    }
