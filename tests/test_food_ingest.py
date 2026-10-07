"""Parser and catalog integration tests."""

from pathlib import Path

from marrow.data.ingest.build import collect_records
from marrow.data.ingest.catalog import catalog_stats, open_catalog, upsert_foods
from marrow.data.ingest.usda import load_usda_json_path
from marrow.data.migrator import current_schema_version, migrate

FIXTURES = Path(__file__).resolve().parents[1] / "marrow" / "data" / "ingest" / "fixtures"


def test_usda_fixture_parses_foods():
    records = load_usda_json_path(FIXTURES / "usda" / "foundation_sample.json")
    assert len(records) == 5
    banana = next(r for r in records if "Banana" in r.name)
    assert banana.nutrients.energy_kcal == 89
    assert len(banana.servings) >= 2


def test_collect_records_fixture_only():
    records = collect_records(use_network=False)
    sources = {r.source for r in records}
    assert sources == {"usda", "off", "ifct"}
    assert len(records) >= 10


def test_catalog_write_and_schema_version(tmp_path):
    records = collect_records(use_network=False)
    db = tmp_path / "catalog.sqlite"
    conn = open_catalog(db)
    try:
        upsert_foods(conn, records)
        stats = catalog_stats(conn)
        assert stats["foods"] == len(records)
        assert current_schema_version(conn) >= 2
        row = conn.execute(
            "SELECT energy_kcal FROM food_nutrients fn "
            "JOIN foods f ON f.id = fn.food_id WHERE f.name LIKE '%Banana%'"
        ).fetchone()
        assert row[0] == 89
    finally:
        conn.close()


def test_migrations_include_food_tables():
    import sqlite3

    conn = sqlite3.connect(":memory:")
    migrate(conn)
    tables = {
        r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    }
    assert "foods" in tables
    assert "food_nutrients" in tables
    assert "food_servings" in tables
    conn.close()
