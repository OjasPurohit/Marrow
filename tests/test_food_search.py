"""FTS5 search behavior."""

from marrow.services.custom_foods import create_custom_food
from marrow.services.food_search import search_foods


def test_search_finds_banana(user_db):
    out = search_foods(user_db, "banana")
    assert out["elapsed_ms"] < 500
    names = [r["name"] for r in out["results"]]
    assert any("Banana" in n for n in names)


def test_search_prefix_as_you_type(user_db):
    out = search_foods(user_db, "ban")
    assert len(out["results"]) >= 1


def test_search_custom_food(user_db):
    create_custom_food(
        user_db,
        "Homemade Protein Bar",
        {"energy_kcal": 400, "protein_g": 20},
    )
    out = search_foods(user_db, "protein bar")
    assert any("Protein Bar" in r["name"] for r in out["results"])


def test_empty_query_returns_no_results(user_db):
    out = search_foods(user_db, "   ")
    assert out["results"] == []
