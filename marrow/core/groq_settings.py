"""Groq API credentials (keyring) and non-secret model settings (config.json)."""

from __future__ import annotations

import os
from typing import Any

import keyring
from keyring.errors import KeyringError

from marrow.core.config import load_config, save_config

KEYRING_SERVICE = "Marrow"
KEYRING_ACCOUNT = "groq_api_key"

DEFAULT_GROQ_SETTINGS: dict[str, Any] = {
    "chat_model": "llama-3.3-70b-versatile",
    "vision_model": "llama-3.2-11b-vision-preview",
    "whisper_model": "whisper-large-v3",
    "request_timeout_sec": 30.0,
    "max_retries": 2,
    "enable_night_summary": True,
    "enable_voice_hotkey": True,
    "voice_hotkey": "ctrl+shift+v",
    "voice_record_seconds": 8.0,
    "enable_photo_parse": True,
}


def _groq_section(cfg: dict[str, Any]) -> dict[str, Any]:
    raw = cfg.get("groq")
    if not isinstance(raw, dict):
        raw = {}
    merged = {**DEFAULT_GROQ_SETTINGS, **raw}
    return merged


def load_groq_settings() -> dict[str, Any]:
    return _groq_section(load_config())


def save_groq_settings(updates: dict[str, Any]) -> dict[str, Any]:
    cfg = load_config()
    section = _groq_section(cfg)
    for key, value in updates.items():
        if key in DEFAULT_GROQ_SETTINGS:
            section[key] = value
    cfg["groq"] = section
    save_config(cfg)
    return section


def get_groq_api_key() -> str | None:
    """Read API key from OS keyring only (never from config.json or SQLite)."""
    try:
        secret = keyring.get_password(KEYRING_SERVICE, KEYRING_ACCOUNT)
    except KeyringError:
        secret = None
    if secret and secret.strip():
        return secret.strip()
    return None


def set_groq_api_key(api_key: str) -> None:
    clean = api_key.strip()
    if not clean:
        raise ValueError("API key cannot be empty")
    try:
        keyring.set_password(KEYRING_SERVICE, KEYRING_ACCOUNT, clean)
    except KeyringError as exc:
        raise RuntimeError(f"Could not store Groq API key in keyring: {exc}") from exc


def clear_groq_api_key() -> None:
    try:
        keyring.delete_password(KEYRING_SERVICE, KEYRING_ACCOUNT)
    except KeyringError:
        pass


def groq_configured() -> bool:
    """True when a Groq key is available (keyring or dev ``GROQ_API_KEY`` env)."""
    return bool(resolve_groq_api_key_for_runtime())


def groq_settings_public() -> dict[str, Any]:
    """Bridge-safe settings snapshot (no secrets)."""
    settings = load_groq_settings()
    return {
        **settings,
        "configured": groq_configured(),
    }


def resolve_groq_api_key_for_runtime() -> str | None:
    """Keyring first; ``GROQ_API_KEY`` env allowed for local dev/CI only."""
    key = get_groq_api_key()
    if key:
        return key
    env = os.environ.get("GROQ_API_KEY", "").strip()
    return env or None
