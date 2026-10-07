"""Diary history summaries for calendar heatmap and day list (M9)."""

from __future__ import annotations

import sqlite3
from collections import defaultdict
from datetime import date, timedelta
from typing import Any

from marrow.services.diary_totals import summarize_diary_nutrients
from marrow.services.user_profile import energy_status_for_day


def _local_today() -> str:
    return date.today().isoformat()


def _parse_iso(day: str) -> date:
    return date.fromisoformat(day)


def _entries_by_date(
    conn: sqlite3.Connection,
    start: str,
    end: str,
) -> dict[str, list[dict[str, Any]]]:
    rows = conn.execute(
        """
        SELECT
            l.log_date,
            e.energy_kcal,
            e.protein_g,
            e.carbs_g,
            e.fat_g
        FROM diary_log_entries e
        JOIN diary_logs l ON l.id = e.log_id
        WHERE l.log_date BETWEEN ? AND ?
        ORDER BY l.log_date ASC, e.id ASC
        """,
        (start, end),
    ).fetchall()
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["log_date"]].append(
            {
                "energy_kcal": row["energy_kcal"],
                "protein_g": row["protein_g"],
                "carbs_g": row["carbs_g"],
                "fat_g": row["fat_g"],
            }
        )
    return grouped


def _summarize_day(
    conn: sqlite3.Connection,
    log_date: str,
    entries: list[dict[str, Any]],
) -> dict[str, Any]:
    nutrients = summarize_diary_nutrients(entries)
    balance = energy_status_for_day(conn, nutrients, log_date)
    entry_count = len(entries)
    logged = entry_count > 0
    data_incomplete = logged and nutrients.get("energy_kcal") is None
    return {
        "log_date": log_date,
        "entry_count": entry_count,
        "logged": logged,
        "data_incomplete": data_incomplete,
        "energy_kcal": nutrients.get("energy_kcal"),
        "protein_g": nutrients.get("protein_g"),
        "energy_balance_status": balance.get("status"),
        "energy_delta_kcal": balance.get("energy_delta_kcal"),
    }


def _compute_streaks(day_summaries: list[dict[str, Any]]) -> dict[str, int]:
    """Summaries must be sorted ascending by log_date."""
    best = 0
    run = 0
    for day in day_summaries:
        if day["logged"]:
            run += 1
            best = max(best, run)
        else:
            run = 0

    current = 0
    for day in reversed(day_summaries):
        if day["logged"]:
            current += 1
        else:
            break

    return {"current": current, "best_in_range": best}


def get_diary_history_range(
    conn: sqlite3.Connection,
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict[str, Any]:
    end = _parse_iso(end_date or _local_today())
    start = _parse_iso(start_date or (end - timedelta(days=89)).isoformat())
    if start > end:
        raise ValueError("start_date must be on or before end_date")

    grouped = _entries_by_date(conn, start.isoformat(), end.isoformat())
    days: list[dict[str, Any]] = []
    cursor = start
    while cursor <= end:
        iso = cursor.isoformat()
        days.append(_summarize_day(conn, iso, grouped.get(iso, [])))
        cursor += timedelta(days=1)

    logged_days = sum(1 for d in days if d["logged"])
    return {
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "days": days,
        "days_logged": logged_days,
        "days_in_range": len(days),
        "streak": _compute_streaks(days),
    }


def get_diary_history_month(
    conn: sqlite3.Connection,
    year: int,
    month: int,
) -> dict[str, Any]:
    if month < 1 or month > 12:
        raise ValueError("month must be 1–12")
    start = date(year, month, 1)
    if month == 12:
        end = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end = date(year, month + 1, 1) - timedelta(days=1)
    payload = get_diary_history_range(conn, start.isoformat(), end.isoformat())
    payload["year"] = year
    payload["month"] = month
    return payload
