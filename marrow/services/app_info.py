"""Read-only app and environment metadata for the UI."""

from __future__ import annotations

import platform
import sys

from marrow import __version__
from marrow.core.paths import app_data_dir, database_path
from marrow.data.database import connect
from marrow.data.migrator import current_schema_version


def get_app_info() -> dict[str, str | int | bool]:
    conn = connect()
    try:
        schema_version = current_schema_version(conn)
    finally:
        conn.close()

    return {
        "name": "Marrow",
        "version": __version__,
        "platform": platform.system(),
        "python": sys.version.split()[0],
        "data_dir": str(app_data_dir()),
        "database_path": str(database_path()),
        "schema_version": schema_version,
        "is_dev": _is_dev(),
    }


def _is_dev() -> bool:
    import os

    return os.environ.get("MARROW_DEV", "").strip() in ("1", "true", "yes")
