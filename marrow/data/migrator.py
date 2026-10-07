"""Apply versioned SQL migrations."""

from __future__ import annotations

import sqlite3
from pathlib import Path

MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"


def _migration_files() -> list[tuple[int, Path]]:
    files: list[tuple[int, Path]] = []
    for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
        version = int(path.stem.split("_", 1)[0])
        files.append((version, path))
    return sorted(files, key=lambda t: t[0])


def ensure_schema_migrations_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version INTEGER PRIMARY KEY,
            applied_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )
    conn.commit()


def applied_versions(conn: sqlite3.Connection) -> set[int]:
    ensure_schema_migrations_table(conn)
    rows = conn.execute("SELECT version FROM schema_migrations").fetchall()
    return {int(r[0]) for r in rows}


def migrate(conn: sqlite3.Connection) -> list[int]:
    """Run pending migrations; returns list of newly applied version numbers."""
    applied = applied_versions(conn)
    newly: list[int] = []
    for version, path in _migration_files():
        if version in applied:
            continue
        sql = path.read_text(encoding="utf-8")
        conn.executescript(sql)
        conn.execute(
            "INSERT OR IGNORE INTO schema_migrations (version) VALUES (?)",
            (version,),
        )
        conn.commit()
        newly.append(version)
    return newly


def current_schema_version(conn: sqlite3.Connection) -> int:
    applied = applied_versions(conn)
    return max(applied) if applied else 0
