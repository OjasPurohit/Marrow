"""Non-secret UI preferences (theme, units, accessibility) in config.json."""

from __future__ import annotations

from typing import Any, Literal

from marrow.core.config import load_config, save_config

ThemeMode = Literal["system", "dark", "light"]
UnitsMode = Literal["metric", "imperial"]
UiScale = Literal["0.875", "1", "1.125", "1.25"]

DEFAULT_USER_SETTINGS: dict[str, Any] = {
    "theme": "system",
    "units": "metric",
    "ui_scale": "1",
    "reduced_motion": False,
    "reduced_transparency": False,
    "higher_contrast": False,
}

_UI_SCALES = frozenset({"0.875", "1", "1.125", "1.25"})
_THEMES = frozenset({"system", "dark", "light"})
_UNITS = frozenset({"metric", "imperial"})


def _ui_section(cfg: dict[str, Any]) -> dict[str, Any]:
    raw = cfg.get("ui")
    if not isinstance(raw, dict):
        raw = {}
    merged = {**DEFAULT_USER_SETTINGS, **raw}
    if merged.get("theme") not in _THEMES:
        merged["theme"] = "system"
    if merged.get("units") not in _UNITS:
        merged["units"] = "metric"
    scale = str(merged.get("ui_scale", "1"))
    if scale not in _UI_SCALES:
        scale = "1"
    merged["ui_scale"] = scale
    for flag in ("reduced_motion", "reduced_transparency", "higher_contrast"):
        merged[flag] = bool(merged.get(flag))
    return merged


def load_user_settings() -> dict[str, Any]:
    return _ui_section(load_config())


def save_user_settings(updates: dict[str, Any]) -> dict[str, Any]:
    cfg = load_config()
    section = _ui_section(cfg)
    for key, value in updates.items():
        if key not in DEFAULT_USER_SETTINGS:
            continue
        if key == "theme" and value in _THEMES:
            section["theme"] = value
        elif key == "units" and value in _UNITS:
            section["units"] = value
        elif key == "ui_scale" and str(value) in _UI_SCALES:
            section["ui_scale"] = str(value)
        elif key in ("reduced_motion", "reduced_transparency", "higher_contrast"):
            section[key] = bool(value)
    cfg["ui"] = section
    save_config(cfg)
    return section


def user_settings_public() -> dict[str, Any]:
    return load_user_settings()
