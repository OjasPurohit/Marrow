"""Profile onboarding and target resolution."""

from datetime import date

from marrow.services.diary_log import list_diary_entries_for_date
from marrow.services.user_profile import (
    complete_onboarding,
    get_user_profile,
    resolve_daily_macro_targets,
    resolve_day_kind,
)


def _onboarding_payload(**overrides):
    base = {
        "age_years": 28,
        "sex": "male",
        "height_cm": 175.0,
        "weight_kg": 72.0,
        "activity_level": "moderate",
        "goal": "maintain",
        "disclaimer_acknowledged": True,
        "use_split_day_targets": True,
        "gym_weekdays": [0, 2, 4],
    }
    base.update(overrides)
    return base


def test_complete_onboarding_persists_targets(user_db):
    profile = complete_onboarding(user_db, _onboarding_payload())
    assert profile["onboarding_completed"]
    assert profile["macro_targets"]["default"]["energy_kcal"] > 0
    assert profile["micronutrient_targets"]["iron_mg"]["target_value"] == 8.0


def test_resolve_gym_vs_rest(user_db):
    complete_onboarding(user_db, _onboarding_payload())
    monday = date(2025, 10, 6)  # Monday
    assert resolve_day_kind(user_db, monday.isoformat()) == "gym"
    tuesday = date(2025, 10, 7)
    assert resolve_day_kind(user_db, tuesday.isoformat()) == "rest"


def test_diary_uses_db_targets_after_onboarding(user_db):
    complete_onboarding(user_db, _onboarding_payload(goal="cut"))
    targets = resolve_daily_macro_targets(user_db)
    day = list_diary_entries_for_date(user_db)
    assert day["totals"]["targets"]["energy_kcal"] == targets["energy_kcal"]
    assert day["totals"]["energy_balance"]["status"] is None


def test_get_profile_before_onboarding(user_db):
    profile = get_user_profile(user_db)
    assert not profile["onboarding_completed"]
