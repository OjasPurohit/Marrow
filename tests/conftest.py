"""Shared pytest fixtures."""

import sqlite3
from pathlib import Path

import pytest

from marrow.data.catalog_seed import ensure_catalog_seeded
from marrow.data.migrator import migrate


@pytest.fixture
def user_db(tmp_path, monkeypatch):
    """Isolated user DB with migrations and bundled catalog seed."""
    db_path = tmp_path / "marrow.db"
    monkeypatch.setattr("marrow.core.paths.database_path", lambda: db_path)
    monkeypatch.setattr("marrow.core.paths.app_data_dir", lambda: tmp_path)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    migrate(conn)
    ensure_catalog_seeded(conn)
    yield conn
    conn.close()
