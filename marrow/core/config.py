"""Persisted user configuration (window geometry, etc.)."""

from __future__ import annotations

import json
from typing import Any

from marrow.core.paths import config_path, default_window_geometry


def load_config() -> dict[str, Any]:
    path = config_path()
    if not path.exists():
        return {"window": default_window_geometry()}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"window": default_window_geometry()}
    if "window" not in data:
        data["window"] = default_window_geometry()
    return data


def save_config(data: dict[str, Any]) -> None:
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def load_window_geometry() -> dict[str, int]:
    cfg = load_config()
    w = cfg.get("window", default_window_geometry())
    defaults = default_window_geometry()
    return {
        "x": int(w.get("x", defaults["x"])),
        "y": int(w.get("y", defaults["y"])),
        "width": int(w.get("width", defaults["width"])),
        "height": int(w.get("height", defaults["height"])),
    }


def save_window_geometry(x: int, y: int, width: int, height: int) -> None:
    cfg = load_config()
    cfg["window"] = {"x": x, "y": y, "width": width, "height": height}
    save_config(cfg)
