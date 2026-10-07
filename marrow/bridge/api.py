"""pywebview `js_api` surface exposed to the frontend."""

from __future__ import annotations

from marrow.core.config import load_window_geometry, save_window_geometry
from marrow.services.app_info import get_app_info


class BridgeApi:
    """Methods are callable from JS via `window.pywebview.api.<name>()`."""

    def ping(self) -> str:
        return "ok"

    def get_app_info(self) -> dict:
        return get_app_info()

    def get_window_geometry(self) -> dict:
        return load_window_geometry()

    def save_window_geometry(self, x: int, y: int, width: int, height: int) -> bool:
        save_window_geometry(int(x), int(y), int(width), int(height))
        return True
