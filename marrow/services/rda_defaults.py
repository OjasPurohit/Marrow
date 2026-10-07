"""Default adult micronutrient targets (RDA-style, editable in profile)."""

from __future__ import annotations

from typing import Literal

Sex = Literal["male", "female"]

# Approximate daily values for adults 19–50; user can override per nutrient.
_BASE_RDA: dict[str, tuple[float, str]] = {
    "fiber_g": (28.0, "g"),
    "sodium_mg": (2300.0, "mg"),
    "potassium_mg": (3400.0, "mg"),
    "calcium_mg": (1000.0, "mg"),
    "iron_mg": (8.0, "mg"),
    "magnesium_mg": (400.0, "mg"),
    "phosphorus_mg": (700.0, "mg"),
    "zinc_mg": (11.0, "mg"),
    "selenium_ug": (55.0, "µg"),
    "vitamin_a_ug": (900.0, "µg"),
    "vitamin_c_mg": (90.0, "mg"),
    "vitamin_d_ug": (15.0, "µg"),
    "vitamin_e_mg": (15.0, "mg"),
    "vitamin_k_ug": (120.0, "µg"),
    "thiamin_mg": (1.2, "mg"),
    "riboflavin_mg": (1.3, "mg"),
    "niacin_mg": (16.0, "mg"),
    "vitamin_b6_mg": (1.3, "mg"),
    "folate_ug": (400.0, "µg"),
    "vitamin_b12_ug": (2.4, "µg"),
}

_SEX_OVERRIDES: dict[Sex, dict[str, float]] = {
    "female": {
        "iron_mg": 18.0,
        "magnesium_mg": 310.0,
        "zinc_mg": 8.0,
    },
    "male": {
        "iron_mg": 8.0,
        "magnesium_mg": 400.0,
        "zinc_mg": 11.0,
    },
}


def default_micronutrient_targets(sex: Sex | None = None) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for key, (value, unit) in _BASE_RDA.items():
        if sex and key in _SEX_OVERRIDES.get(sex, {}):
            value = _SEX_OVERRIDES[sex][key]
        out[key] = {"target_value": value, "unit": unit}
    return out
