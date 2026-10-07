"""Night review aggregation (M7)."""

from datetime import date

from marrow.services.diary_log import confirm_and_save_log, list_diary_entries_for_date
from marrow.services.diary_parse import parse_food_text
from marrow.services.night_review import (
    aggregate_night_review,
    build_scaled_diary_entries,
    estimated_calorie_share,
    flag_nutrient,
    get_night_review,
    macro_calorie_split,
    sum_nutrients_with_coverage,
    top_contributors_per_nutrient,
)
from marrow.services.user_profile import complete_onboarding


def test_sum_nutrients_with_coverage_partial():
    entries = [
        {
            "food_name": "A",
            "food_id": 1,
            "nutrients": {"iron_mg": 2.0, "energy_kcal": 100.0},
        },
        {
            "food_name": "B",
            "food_id": 2,
            "nutrients": {"iron_mg": None, "energy_kcal": 50.0},
        },
        {
            "food_name": "C",
            "food_id": 3,
            "nutrients": {"iron_mg": 1.0, "energy_kcal": 25.0},
        },
    ]
    totals, coverage = sum_nutrients_with_coverage(entries)
    assert totals["iron_mg"] == 3.0
    assert coverage["iron_mg"] == {"with_data": 2, "missing": 1}
    assert totals["energy_kcal"] == 175.0


def test_top_contributors_orders_desc():
    entries = [
        {"food_name": "Spinach", "food_id": 1, "nutrients": {"iron_mg": 1.0}},
        {"food_name": "Lentils", "food_id": 2, "nutrients": {"iron_mg": 4.0}},
        {"food_name": "Rice", "food_id": 3, "nutrients": {"iron_mg": 0.5}},
    ]
    tops = top_contributors_per_nutrient(entries, limit=2)
    assert tops["iron_mg"][0]["food_name"] == "Lentils"
    assert tops["iron_mg"][1]["food_name"] == "Spinach"


def test_macro_calorie_split():
    split = macro_calorie_split({"protein_g": 100.0, "carbs_g": 100.0, "fat_g": 100.0})
    assert split["protein_pct"] == 23.5
    assert split["carbs_pct"] == 23.5
    assert split["fat_pct"] == 52.9


def test_estimated_calorie_share():
    entries = [
        {"energy_kcal": 200.0, "match_confidence": "ESTIMATED"},
        {"energy_kcal": 300.0, "match_confidence": "EXACT"},
        {"energy_kcal": None, "match_confidence": "ESTIMATED"},
    ]
    est = estimated_calorie_share(entries)
    assert est["known_kcal"] == 500.0
    assert est["estimated_kcal"] == 200.0
    assert est["estimated_pct_of_known"] == 40.0


def test_flag_nutrient_low_and_high():
    assert flag_nutrient("iron_mg", 5.0, 10.0) == "low"
    assert flag_nutrient("iron_mg", 25.0, 10.0) == "high"
    assert flag_nutrient("sodium_mg", 3000.0, 2300.0) == "high"
    assert flag_nutrient("sodium_mg", 1000.0, 2300.0) is None


def test_aggregate_summary_mentions_deficit():
    review = aggregate_night_review(
        scaled_entries=[],
        diary_entries=[{"energy_kcal": 100.0, "match_confidence": "EXACT"}],
        macro_totals={"energy_kcal": 100.0, "protein_g": 10.0, "carbs_g": 10.0, "fat_g": 2.0},
        targets={"energy_kcal": {"target_value": 2200.0, "unit": "kcal"}},
        energy_balance={"status": "DEFICIT", "energy_delta_kcal": -500.0},
    )
    assert any("under" in line for line in review["summary_lines"])


def test_get_night_review_integration(user_db):
    complete_onboarding(
        user_db,
        {
            "age_years": 28,
            "sex": "male",
            "height_cm": 178.0,
            "weight_kg": 75.0,
            "activity_level": "moderate",
            "goal": "maintain",
            "disclaimer_acknowledged": True,
        },
    )
    parsed = parse_food_text(user_db, "2 roti", meal_tag="dinner")
    item = parsed["items"][0]
    confirm_and_save_log(
        user_db,
        {
            "log_date": date.today().isoformat(),
            "meal_tag": "dinner",
            "items": [
                {
                    "food_id": item["food_id"],
                    "amount": item["amount"],
                    "unit": item["unit"],
                    "match_confidence": "ESTIMATED",
                }
            ],
        },
    )
    day = list_diary_entries_for_date(user_db)
    scaled = build_scaled_diary_entries(user_db, day["entries"])
    assert scaled[0]["nutrients"]["energy_kcal"] is not None

    review = get_night_review(user_db)
    assert review["entry_count"] == 1
    assert review["energy_balance"]["status"] is not None
    assert len(review["nutrients"]) > 0
    assert review["estimated_confidence"]["estimated_pct_of_known"] == 100.0
    iron_row = next(r for r in review["nutrients"] if r["key"] == "iron_mg")
    assert iron_row["label"] == "Iron"
    assert review["groq_summary"] is None
