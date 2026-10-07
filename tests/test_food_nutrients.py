"""Nutrient mapping tests."""

from marrow.data.foods.nutrients import (
    nutrients_from_ifct_row,
    nutrients_from_off_nutriments,
    nutrients_from_usda_entries,
)


def test_usda_nutrient_id_mapping():
    entries = [
        {"nutrient": {"id": 1008}, "amount": 89},
        {"nutrient": {"id": 1003}, "amount": 1.1},
    ]
    values = nutrients_from_usda_entries(entries)
    assert values.energy_kcal == 89
    assert values.protein_g == 1.1
    assert values.fat_g is None


def test_off_nutriments_per_100g():
    values = nutrients_from_off_nutriments(
        {"energy-kcal_100g": 250, "proteins_100g": 8, "fat_100g": 12}
    )
    assert values.energy_kcal == 250
    assert values.protein_g == 8
    assert values.fat_g == 12


def test_off_sodium_grams_to_milligrams():
    values = nutrients_from_off_nutriments({"sodium_100g": 0.4})
    assert values.sodium_mg == 400.0


def test_ifct_row_parsing():
    row = {
        "energy_kcal": "104",
        "protein_g": "7.0",
        "carbs_g": "17.7",
        "fat_g": "-",
        "fiber_g": "",
        "calcium_mg": "22",
        "iron_mg": "1.5",
        "vitamin_c_mg": "1.2",
    }
    values = nutrients_from_ifct_row(row)
    assert values.energy_kcal == 104
    assert values.fat_g is None
    assert values.iron_mg == 1.5
