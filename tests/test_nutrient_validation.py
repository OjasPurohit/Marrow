"""Nutrient validation rules."""

from marrow.services.nutrient_validation import (
    collect_nutrient_warnings,
    macro_kcal_consistent,
)


def test_macro_kcal_within_tolerance():
    assert macro_kcal_consistent(100, 10, 10, 2.2) is True
    assert macro_kcal_consistent(500, 10, 10, 2.2) is False


def test_portion_warning():
    warnings = collect_nutrient_warnings(
        energy_kcal=100,
        protein_g=5,
        carbs_g=10,
        fat_g=2,
        grams_equivalent=2000,
    )
    assert "portion_very_large" in warnings
