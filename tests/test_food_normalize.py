"""Normalization and data-quality scoring tests."""

from marrow.data.foods.nutrients import NutrientValues
from marrow.data.ingest.normalize import (
    infer_preparation,
    normalize_food_name,
    score_data_quality,
    slug_for_search,
)


def test_normalize_food_name_strips_accents_and_case():
    assert normalize_food_name("  Café au Lait  ") == "cafe au lait"


def test_slug_for_search_alphanumeric():
    assert slug_for_search("Banana, raw!") == "banana raw"


def test_infer_preparation_keywords():
    assert infer_preparation("Rice, white, cooked") == "cooked"
    assert infer_preparation("Spinach, raw") == "raw"
    assert infer_preparation("Mystery food") == "unknown"


def test_score_data_quality_usda_high():
    nutrients = NutrientValues(
        energy_kcal=100,
        protein_g=5,
        carbs_g=10,
        fat_g=2,
        iron_mg=1,
        calcium_mg=2,
        vitamin_c_mg=3,
        sodium_mg=4,
        potassium_mg=5,
        fiber_g=6,
        sugar_g=7,
        magnesium_mg=8,
        phosphorus_mg=9,
    )
    assert score_data_quality("usda", nutrients, branded=False) == "high"
