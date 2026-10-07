"""Diary history and trends (M9)."""

from datetime import date, timedelta

from marrow.services.diary_history import get_diary_history_range
from marrow.services.diary_log import confirm_and_save_log
from marrow.services.diary_parse import parse_food_text
from marrow.services.trends import get_trend_series
from marrow.services.weight_log import (
    add_weight_entry,
    delete_weight_entry,
    smooth_weight_trend,
)


def _save_day(conn, log_date: str, text: str = "100g rice"):
    parsed = parse_food_text(conn, text, meal_tag="lunch")
    items = [
        {
            "food_id": item["food_id"],
            "amount": item["amount"],
            "unit": item["unit"],
            "match_confidence": item.get("match_confidence"),
        }
        for item in parsed["items"]
        if item.get("food_id") is not None
    ]
    assert items
    confirm_and_save_log(
        conn,
        {"log_date": log_date, "meal_tag": "lunch", "items": items},
    )


def test_history_streak_and_logged_days(user_db):
    today = date.today()
    d1 = (today - timedelta(days=2)).isoformat()
    d2 = (today - timedelta(days=1)).isoformat()
    d3 = today.isoformat()
    _save_day(user_db, d1)
    _save_day(user_db, d2)
    _save_day(user_db, d3)

    history = get_diary_history_range(user_db, start_date=d1, end_date=d3)
    assert history["days_logged"] == 3
    assert history["streak"]["current"] == 3
    assert all(day["logged"] for day in history["days"])


def test_history_marks_empty_days(user_db):
    today = date.today().isoformat()
    history = get_diary_history_range(user_db, start_date=today, end_date=today)
    assert history["days"][0]["logged"] is False
    assert history["days"][0]["entry_count"] == 0


def test_trend_series_rolling_and_weight(user_db):
    today = date.today()
    for offset in range(3):
        day = (today - timedelta(days=offset)).isoformat()
        _save_day(user_db, day)
        add_weight_entry(user_db, 70.0 + offset * 0.1, logged_date=day)

    trends = get_trend_series(user_db, range_days=7)
    assert trends["range_days"] == 7
    assert len(trends["dates"]) == 7
    assert trends["days_logged"] == 3
    assert any(v is not None for v in trends["rolling_7_energy_kcal"])
    assert any(v is not None for v in trends["weight_kg"])


def test_smooth_weight_trend():
    smooth = smooth_weight_trend(
        [
            {"weight_kg": 70.0},
            {"weight_kg": 71.0},
            {"weight_kg": None},
            {"weight_kg": 72.0},
        ],
        window=2,
    )
    assert smooth[0] == 70.0
    assert smooth[1] == 70.5
    assert smooth[2] == 71.0
    assert smooth[3] == 72.0


def test_delete_weight_entry(user_db):
    row = add_weight_entry(user_db, 68.5)
    delete_weight_entry(user_db, row["id"])
    from marrow.services.weight_log import list_weight_entries

    assert list_weight_entries(user_db) == []
