"""Application data paths (never inside install dir or repo)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

APP_NAME = "Marrow"


def app_data_dir() -> Path:
    """Return the per-user application data directory."""
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA")
        if not base:
            base = Path.home() / "AppData" / "Local"
        else:
            base = Path(base)
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        xdg = os.environ.get("XDG_DATA_HOME")
        base = Path(xdg) if xdg else Path.home() / ".local" / "share"

    path = Path(base) / APP_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def database_path() -> Path:
    return app_data_dir() / "marrow.db"


def repo_root() -> Path:
    """Repository root (for bundled dev assets)."""
    return Path(__file__).resolve().parents[2]


def bundled_foods_catalog_path() -> Path:
    """Pre-built offline food subset shipped with the app for dev/demo."""
    return repo_root() / "marrow" / "data" / "processed" / "foods_catalog.sqlite"


def config_path() -> Path:
    return app_data_dir() / "config.json"


def backups_dir() -> Path:
    path = app_data_dir() / "backups"
    path.mkdir(parents=True, exist_ok=True)
    return path


def default_window_geometry() -> dict[str, int]:
    return {"x": 100, "y": 100, "width": 1200, "height": 800}
