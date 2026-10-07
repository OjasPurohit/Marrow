"""Migration tests."""

import sqlite3
import tempfile
from pathlib import Path

import pytest

from marrow.core.paths import migrations_dir
from marrow.data.migrator import migrate, current_schema_version


@pytest.fixture
def memory_conn():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()


def test_migrations_apply(memory_conn, monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        mig_dir = Path(tmp)
        (mig_dir / "001_initial.sql").write_text(
            "CREATE TABLE t (id INTEGER PRIMARY KEY);",
            encoding="utf-8",
        )
        monkeypatch.setattr("marrow.data.migrator.migrations_dir", lambda: mig_dir)
        applied = migrate(memory_conn)
        assert applied == [1]
        assert current_schema_version(memory_conn) == 1
        # Idempotent
        assert migrate(memory_conn) == []


def test_real_migrations_exist():
    mig = migrations_dir()
    assert mig.exists()
    files = list(mig.glob("*.sql"))
    assert len(files) >= 1
