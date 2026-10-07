"""Bundled catalog import."""

from marrow.data.catalog_seed import catalog_seed_status, ensure_catalog_seeded
from marrow.data.migrator import migrate


def test_catalog_seed_imports_foods(user_db):
    count = user_db.execute("SELECT COUNT(*) FROM foods").fetchone()[0]
    assert count >= 10
    status = catalog_seed_status(user_db)
    assert status["needs_seed"] is False
    assert ensure_catalog_seeded(user_db) == 0
