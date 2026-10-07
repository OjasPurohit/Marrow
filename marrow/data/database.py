"""SQLite connection lifecycle."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from typing import Iterator

from marrow.core.paths import database_path
from marrow.data.catalog_seed import ensure_catalog_seeded
from marrow.data.migrator import migrate
from marrow.services.backup import maybe_automatic_backup


def connect() -> sqlite3.Connection:
    path = database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    migrate(conn)
    ensure_catalog_seeded(conn)
    try:
        maybe_automatic_backup()
    except OSError:
        pass
    return conn


@contextmanager
def session() -> Iterator[sqlite3.Connection]:
    conn = connect()
    try:
        yield conn
    finally:
        conn.close()
