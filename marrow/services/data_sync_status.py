"""Honest data-source / catalog sync status for Settings."""

from __future__ import annotations

import sqlite3

from marrow.data.catalog_seed import catalog_seed_status


def get_data_sync_status(conn: sqlite3.Connection) -> dict:
    seed = catalog_seed_status(conn)
    bundled_count = int(seed.get("catalog_food_count") or 0)
    return {
        **seed,
        "mode": "bundled_catalog",
        "full_sync_available": False,
        "summary": (
            f"Offline bundled food catalog ({bundled_count} catalog foods in your database). "
            "Full USDA / Open Food Facts sync is not enabled in this build — rebuild the catalog "
            "via scripts/build_food_catalog.py for developer datasets."
        ),
        "last_sync_at": None,
        "sync_state": "up_to_date" if not seed.get("needs_seed") else "seed_pending",
    }
