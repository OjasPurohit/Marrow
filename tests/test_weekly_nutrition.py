"""Weekly rolling nutrition averages."""

from datetime import date, timedelta

from marrow.services.diary_log import confirm_and_save_log
from marrow.services.diary_parse import parse_food_text
from marrow.services.weekly_nutrition import get_weekly_nutrition_average


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


def test_weekly_average_locked_until_seven_days(user_db):
    today = date.today()
    start = today - timedelta(days=6)
    for i in range(6):
        d = (start + timedelta(days=i)).isoformat()
        _save_day(user_db, d)

    payload = get_weekly_nutrition_average(user_db, end_date=today.isoformat())
    assert not payload["eligible"]
    assert payload["days_logged"] == 6
    assert payload["days_remaining"] == 1

    _save_day(user_db, today.isoformat())
    payload = get_weekly_nutrition_average(user_db, end_date=today.isoformat())
    assert payload["eligible"]
    assert payload["macros_avg"]["energy_kcal"] is not None
