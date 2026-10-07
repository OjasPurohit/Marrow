"""Serving conversion math."""

import pytest

from marrow.data.foods.units import (
    convert_to_basis_amount,
    preparation_adjustment_factor,
    scale_nutrients,
)


def test_mass_and_volume_to_grams():
    c = convert_to_basis_amount(2, "kg", basis="per_100g", food_name="Test", preparation="unknown")
    assert c.grams_equivalent == 2000.0

    cup = convert_to_basis_amount(
        1, "cup", basis="per_100g", food_name="Water", preparation="unknown"
    )
    assert cup.grams_equivalent == 240.0


def test_food_serving_match():
    servings = [
        {
            "label": "1 medium",
            "amount": 1.0,
            "unit": "medium",
            "grams_equivalent": 118.0,
            "is_default": True,
            "sort_order": 1,
        }
    ]
    c = convert_to_basis_amount(
        1,
        "medium",
        basis="per_100g",
        food_name="Banana",
        preparation="raw",
        food_servings=servings,
    )
    assert c.matched_food_serving is True
    assert c.grams_equivalent == 118.0


def test_indian_default_piece_weights():
    c = convert_to_basis_amount(
        2, "roti", basis="per_100g", food_name="Chapati", preparation="cooked"
    )
    assert c.grams_equivalent == 80.0
    assert c.note == "default_piece_weight"


def test_raw_cooked_rice_factor():
    factor = preparation_adjustment_factor("Rice, white, raw", "raw", "cooked")
    assert factor == 2.8


def test_scale_nutrients():
    per_100 = {"energy_kcal": 100.0, "protein_g": 10.0}
    scaled = scale_nutrients(per_100, 50.0)
    assert scaled["energy_kcal"] == 50.0
    assert scaled["protein_g"] == 5.0


def test_unknown_unit_raises():
    with pytest.raises(ValueError, match="unknown unit"):
        convert_to_basis_amount(
            1, "furlong", basis="per_100g", food_name="X", preparation="unknown"
        )
