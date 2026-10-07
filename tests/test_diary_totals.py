"""Daily diary nutrient aggregation."""

from marrow.services.diary_totals import (
    PLACEHOLDER_DAILY_TARGETS,
    group_entries_by_meal,
    remaining_budget,
    summarize_diary_nutrients,
)


def test_summarize_all_known():
    entries = [
        {"energy_kcal": 100.0, "protein_g": 10.0, "carbs_g": 12.0, "fat_g": 3.0},
        {"energy_kcal": 50.0, "protein_g": 5.0, "carbs_g": 6.0, "fat_g": 2.0},
    ]
    totals = summarize_diary_nutrients(entries)
    assert totals == {
        "energy_kcal": 150.0,
        "protein_g": 15.0,
        "carbs_g": 18.0,
        "fat_g": 5.0,
    }


def test_summarize_null_propagates():
    entries = [
        {"energy_kcal": 100.0, "protein_g": 10.0, "carbs_g": 12.0, "fat_g": 3.0},
        {"energy_kcal": None, "protein_g": 5.0, "carbs_g": 6.0, "fat_g": 2.0},
    ]
    totals = summarize_diary_nutrients(entries)
    assert totals["energy_kcal"] is None
    assert totals["protein_g"] == 15.0


def test_summarize_empty():
    assert summarize_diary_nutrients([]) == {
        "energy_kcal": None,
        "protein_g": None,
        "carbs_g": None,
        "fat_g": None,
    }


def test_remaining_budget():
    consumed = {"energy_kcal": 500.0, "protein_g": 40.0, "carbs_g": None, "fat_g": 20.0}
    rem = remaining_budget(consumed, PLACEHOLDER_DAILY_TARGETS)
    assert rem["energy_kcal"] == PLACEHOLDER_DAILY_TARGETS["energy_kcal"] - 500.0
    assert rem["carbs_g"] is None


def test_group_entries_by_meal_order():
    entries = [
        {"meal_tag": "dinner", "energy_kcal": 1},
        {"meal_tag": "breakfast", "energy_kcal": 2},
        {"meal_tag": "lunch", "energy_kcal": 3},
    ]
    sections = group_entries_by_meal(entries)
    assert [s["meal_tag"] for s in sections] == ["breakfast", "lunch", "dinner"]
    assert sections[0]["totals"]["energy_kcal"] == 2.0


def test_list_day_includes_macros(user_db):
    from datetime import date

    from marrow.services.diary_log import confirm_and_save_log, list_diary_entries_for_date
    from marrow.services.diary_parse import parse_food_text

    parsed = parse_food_text(user_db, "2 roti", meal_tag="lunch")
    item = parsed["items"][0]
    confirm_and_save_log(
        user_db,
        {
            "log_date": date.today().isoformat(),
            "meal_tag": "lunch",
            "items": [
                {
                    "food_id": item["food_id"],
                    "amount": item["amount"],
                    "unit": item["unit"],
                    "match_confidence": item["match_confidence"],
                }
            ],
        },
    )
    day = list_diary_entries_for_date(user_db)
    assert day["totals"]["protein_g"] is not None
    assert day["totals"]["targets"]["energy_kcal"] == PLACEHOLDER_DAILY_TARGETS["energy_kcal"]
    assert len(day["meals"]) == 1
    assert day["meals"][0]["meal_tag"] == "lunch"
