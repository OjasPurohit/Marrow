"""BMR/TDEE and macro suggestion tests."""

from marrow.services.metabolism import (
    goal_energy_target,
    mifflin_st_jeor_bmr,
    suggest_macro_targets,
    tdee_from_bmr,
)


def test_mifflin_st_jeor_male_reference():
    bmr = mifflin_st_jeor_bmr(
        weight_kg=80.0,
        height_cm=180.0,
        age_years=30,
        sex="male",
    )
    assert bmr == 1780.0


def test_mifflin_st_jeor_female_reference():
    bmr = mifflin_st_jeor_bmr(
        weight_kg=60.0,
        height_cm=165.0,
        age_years=30,
        sex="female",
    )
    assert bmr == 1320.25


def test_tdee_moderate_activity():
    bmr = 1500.0
    assert tdee_from_bmr(bmr, "moderate") == 2325.0


def test_cut_guardrail_female():
    energy, warnings = goal_energy_target(1300.0, "cut", "female")
    assert energy == 1200.0
    assert warnings


def test_cut_no_guardrail_when_high_tdee():
    energy, warnings = goal_energy_target(2500.0, "cut", "male")
    assert energy == 2100.0
    assert not warnings


def test_suggest_macros_sum_reasonable():
    macros = suggest_macro_targets(2000.0, 70.0, "maintain")
    assert macros["protein_g"] == 112.0
    kcal = (
        macros["protein_g"] * 4
        + macros["carbs_g"] * 4
        + macros["fat_g"] * 9
    )
    assert 1900 <= kcal <= 2050
