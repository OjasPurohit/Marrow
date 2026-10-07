"""Mifflin-St Jeor BMR/TDEE and suggested macro splits (M6)."""

from __future__ import annotations

from typing import Literal

Sex = Literal["male", "female"]
ActivityLevel = Literal["sedentary", "light", "moderate", "active", "very_active"]
Goal = Literal["cut", "maintain", "lean_bulk"]

ACTIVITY_MULTIPLIERS: dict[str, float] = {
    "sedentary": 1.2,
    "light": 1.375,
    "moderate": 1.55,
    "active": 1.725,
    "very_active": 1.9,
}

GOAL_CALORIE_ADJUST_KCAL: dict[str, float] = {
    "cut": -400.0,
    "maintain": 0.0,
    "lean_bulk": 250.0,
}

GYM_DAY_EXTRA_KCAL = 200.0

PROTEIN_G_PER_KG: dict[str, float] = {
    "cut": 2.0,
    "maintain": 1.6,
    "lean_bulk": 1.8,
}

MIN_DAILY_KCAL: dict[str, float] = {
    "female": 1200.0,
    "male": 1500.0,
}

MEDICAL_DISCLAIMER = (
    "Marrow provides estimates for personal tracking only — not medical advice. "
    "Consult a qualified professional before changing your diet, especially if you "
    "have a health condition."
)


def mifflin_st_jeor_bmr(
    *,
    weight_kg: float,
    height_cm: float,
    age_years: int,
    sex: Sex,
) -> float:
    base = 10.0 * weight_kg + 6.25 * height_cm - 5.0 * age_years
    return base + 5.0 if sex == "male" else base - 161.0


def tdee_from_bmr(bmr: float, activity_level: ActivityLevel) -> float:
    mult = ACTIVITY_MULTIPLIERS.get(activity_level, ACTIVITY_MULTIPLIERS["moderate"])
    return bmr * mult


def goal_energy_target(
    tdee: float,
    goal: Goal,
    sex: Sex,
) -> tuple[float, list[str]]:
    """Return rounded daily kcal target and any guardrail warnings."""
    warnings: list[str] = []
    raw = tdee + GOAL_CALORIE_ADJUST_KCAL[goal]
    floor = MIN_DAILY_KCAL[sex]
    if raw < floor:
        warnings.append(
            f"Suggested intake was raised to {int(floor)} kcal (minimum guardrail for {sex})."
        )
        raw = floor
    return round(raw, 0), warnings


def suggest_macro_targets(
    energy_kcal: float,
    weight_kg: float,
    goal: Goal,
) -> dict[str, float]:
    protein_g = round(weight_kg * PROTEIN_G_PER_KG[goal], 1)
    protein_kcal = protein_g * 4.0
    fat_g = round(max(weight_kg * 0.8, 40.0), 1)
    fat_kcal = fat_g * 9.0
    remaining = max(0.0, energy_kcal - protein_kcal - fat_kcal)
    carbs_g = round(remaining / 4.0, 1)
    return {
        "energy_kcal": round(energy_kcal, 0),
        "protein_g": protein_g,
        "carbs_g": carbs_g,
        "fat_g": fat_g,
    }


def compute_metabolic_plan(
    *,
    age_years: int,
    sex: Sex,
    height_cm: float,
    weight_kg: float,
    activity_level: ActivityLevel,
    goal: Goal,
) -> dict:
    bmr = mifflin_st_jeor_bmr(
        weight_kg=weight_kg,
        height_cm=height_cm,
        age_years=age_years,
        sex=sex,
    )
    tdee = tdee_from_bmr(bmr, activity_level)
    energy_kcal, warnings = goal_energy_target(tdee, goal, sex)
    macros = suggest_macro_targets(energy_kcal, weight_kg, goal)
    gym_macros = suggest_macro_targets(
        energy_kcal + GYM_DAY_EXTRA_KCAL, weight_kg, goal
    )
    return {
        "bmr_kcal": round(bmr, 1),
        "tdee_kcal": round(tdee, 1),
        "suggested_default": macros,
        "suggested_gym": gym_macros,
        "suggested_rest": macros,
        "warnings": warnings,
        "disclaimer": MEDICAL_DISCLAIMER,
    }
