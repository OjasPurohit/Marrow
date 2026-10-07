"""Rolling 7-day macro/micro averages after a full week of logging."""

from __future__ import annotations

import sqlite3
from datetime import date, timedelta
from typing import Any

from marrow.services.diary_history import _entries_by_date, _summarize_day
from marrow.services.diary_totals import MACRO_KEYS, summarize_diary_nutrients
from marrow.services.trends import _micro_series_for_day

WEEK_DAYS = 7
DISPLAY_MICRO_KEYS = ("fiber_g", "iron_mg", "calcium_mg", "vitamin_d_ug", "sodium_mg")

MICRO_LABELS: dict[str, str] = {
    "fiber_g": "Fiber",
    "iron_mg": "Iron",
    "calcium_mg": "Calcium",
    "vitamin_d_ug": "Vitamin D",
    "sodium_mg": "Sodium",
}


def _local_today() -> str:
    return date.today().isoformat()


def _average(values: list[float | None]) -> float | None:
    nums = [float(v) for v in values if v is not None]
    if not nums:
        return None
    return round(sum(nums) / len(nums), 1)


def get_weekly_nutrition_average(
    conn: sqlite3.Connection,
    end_date: str | None = None,
) -> dict[str, Any]:
    """Average daily intake over the last 7 calendar days when every day has logs."""
    end = date.fromisoformat(end_date or _local_today())
    start = end - timedelta(days=WEEK_DAYS - 1)
    grouped = _entries_by_date(conn, start.isoformat(), end.isoformat())

    day_rows: list[dict[str, Any]] = []
    cursor = start
    while cursor <= end:
        iso = cursor.isoformat()
        entries = grouped.get(iso, [])
        day_rows.append(_summarize_day(conn, iso, entries))
        cursor += timedelta(days=1)

    days_logged = sum(1 for d in day_rows if d["logged"])
    days_remaining = max(0, WEEK_DAYS - days_logged)
    eligible = days_logged >= WEEK_DAYS

    payload: dict[str, Any] = {
        "window_days": WEEK_DAYS,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "days_logged": days_logged,
        "days_remaining": days_remaining,
        "eligible": eligible,
        "macros_avg": {key: None for key in MACRO_KEYS},
        "micros_avg": {key: None for key in DISPLAY_MICRO_KEYS},
        "micro_labels": dict(MICRO_LABELS),
    }

    if not eligible:
        return payload

    payload["macros_avg"] = {
        key: _average([d.get(key) for d in day_rows if d["logged"]]) for key in MACRO_KEYS
    }

    micro_by_day: dict[str, list[float | None]] = {key: [] for key in DISPLAY_MICRO_KEYS}
    for day in day_rows:
        if not day["logged"]:
            continue
        row = _micro_series_for_day(conn, day["log_date"], DISPLAY_MICRO_KEYS)
        for key in DISPLAY_MICRO_KEYS:
            micro_by_day[key].append(row.get(key))

    payload["micros_avg"] = {key: _average(micro_by_day[key]) for key in DISPLAY_MICRO_KEYS}
    return payload
