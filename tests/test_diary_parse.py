"""Diary parse + save integration."""

from datetime import date

from marrow.services.diary_log import confirm_and_save_log, list_diary_entries_for_date
from marrow.services.diary_parse import parse_food_text


SAMPLE_SENTENCES = [
    "2 roti and 1 katori dal",
    "1/2 cup rice",
    "do idli",
    "1 medium banana",
]


def test_parse_food_text_samples(user_db):
    for sentence in SAMPLE_SENTENCES:
        result = parse_food_text(user_db, sentence, meal_tag="lunch")
        assert result["parser"] == "local"
        assert result["groq_used"] is False
        assert len(result["items"]) >= 1
        for item in result["items"]:
            assert item["raw_fragment"]
            if item["food_id"] is not None:
                assert item["energy_kcal"] is None or item["energy_kcal"] >= 0
                assert item["match_confidence"] in ("EXACT", "GOOD", "ESTIMATED")


def test_confirm_and_list_today(user_db):
    parsed = parse_food_text(user_db, "2 roti", meal_tag="breakfast")
    assert parsed["items"]
    item = parsed["items"][0]
    assert item["food_id"] is not None

    saved = confirm_and_save_log(
        user_db,
        {
            "log_date": date.today().isoformat(),
            "meal_tag": "breakfast",
            "source_text": "2 roti",
            "items": [
                {
                    "food_id": item["food_id"],
                    "amount": item["amount"],
                    "unit": item["unit"],
                    "match_confidence": item["match_confidence"],
                    "raw_fragment": item["raw_fragment"],
                }
            ],
        },
    )
    assert saved["log_id"] > 0
    assert saved["entries"][0]["energy_kcal"] is not None

    day = list_diary_entries_for_date(user_db, date.today().isoformat())
    assert day["totals"]["entry_count"] == 1
    assert day["entries"][0]["food_name"]
