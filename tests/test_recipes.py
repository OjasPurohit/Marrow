"""Recipe nutrient aggregation."""

import pytest

from marrow.services.custom_foods import create_custom_food
from marrow.services.recipes import aggregate_recipe_nutrients, create_recipe


def test_recipe_aggregates_macros(user_db):
    a = create_custom_food(user_db, "Ingredient A", {"energy_kcal": 100, "protein_g": 10})
    b = create_custom_food(user_db, "Ingredient B", {"energy_kcal": 200, "carbs_g": 30})
    total = aggregate_recipe_nutrients(
        user_db,
        [
            {"food_id": a["id"], "grams": 100},
            {"food_id": b["id"], "grams": 50},
        ],
    )
    assert total["energy_kcal"] == 200.0
    assert total["protein_g"] == 10.0
    assert total["carbs_g"] == 15.0


def test_create_recipe_per_serving(user_db):
    foods = user_db.execute("SELECT id FROM foods LIMIT 2").fetchall()
    assert len(foods) >= 2
    recipe = create_recipe(
        user_db,
        "Test Bowl",
        2,
        [
            {"food_id": foods[0][0], "grams": 100},
            {"food_id": foods[1][0], "grams": 100},
        ],
    )
    assert recipe["servings_count"] == 2
    assert len(recipe["ingredients"]) == 2
    assert recipe["nutrients_per_serving"]["energy_kcal"] is not None
    assert recipe["nutrients_total"]["energy_kcal"] == pytest.approx(
        recipe["nutrients_per_serving"]["energy_kcal"] * 2,
        rel=1e-3,
    )
