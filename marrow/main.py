"""Marrow desktop entry — pywebview shell."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from marrow.bridge.api import BridgeApi
from marrow.core.config import load_window_geometry, save_window_geometry
from marrow.data.database import connect
from marrow.services.voice_input import start_voice_hotkey_listener


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _ui_url() -> str:
    dev = os.environ.get("MARROW_DEV", "").strip() in ("1", "true", "yes")
    dist_index = _repo_root() / "ui" / "dist" / "index.html"
    if dev or not dist_index.exists():
        port = os.environ.get("MARROW_VITE_PORT", "5173")
        return f"http://127.0.0.1:{port}"
    return dist_index.as_uri()


def _check_webview2_runtime() -> str | None:
    """Return user-facing error message if WebView2 is required but missing."""
    if sys.platform != "win32":
        return None
    try:
        import webview  # noqa: F401
    except ImportError:
        return (
            "Marrow could not load the WebView module. "
            "Reinstall the application or run: pip install pywebview"
        )
    # pywebview on Windows uses pythonnet + WebView2; missing runtime surfaces at create_window.
    return None


def _persist_window(window) -> None:
    try:
        save_window_geometry(window.x, window.y, window.width, window.height)
    except Exception:
        pass


def run() -> int:
    preflight = _check_webview2_runtime()
    if preflight:
        print(preflight, file=sys.stderr)
        _show_native_error(preflight)
        return 1

    # Ensure database and migrations run before UI loads.
    conn = connect()
    conn.close()

    import webview

    geom = load_window_geometry()
    api = BridgeApi()
    url = _ui_url()

    window = webview.create_window(
        "Marrow",
        url=url,
        js_api=api,
        width=geom["width"],
        height=geom["height"],
        x=geom["x"],
        y=geom["y"],
        min_size=(900, 600),
        background_color="#0d0d0f",
    )

    def on_closing():
        _persist_window(window)

    window.events.closing += on_closing

    def _push_voice_transcript(text: str) -> None:
        try:
            safe = text.replace("\\", "\\\\").replace("'", "\\'").replace("\n", " ")
            window.evaluate_js(
                f"window.dispatchEvent(new CustomEvent('marrow-voice-transcript', "
                f"{{detail:{{text:'{safe}'}}}}));"
            )
        except Exception:
            pass

    start_voice_hotkey_listener(on_text=_push_voice_transcript)

    try:
        webview.start(debug=_is_debug())
    except Exception as exc:
        msg = str(exc).lower()
        if "webview2" in msg or "edge" in msg or "runtime" in msg:
            text = (
                "Microsoft Edge WebView2 is required to run Marrow.\n\n"
                "Install it from:\n"
                "https://developer.microsoft.com/microsoft-edge/webview2/\n\n"
                f"Details: {exc}"
            )
            _show_native_error(text)
            return 1
        raise
    return 0


def _is_debug() -> bool:
    return os.environ.get("MARROW_DEV", "").strip() in ("1", "true", "yes")


def _show_native_error(message: str) -> None:
    if sys.platform == "win32":
        try:
            import ctypes

            ctypes.windll.user32.MessageBoxW(0, message, "Marrow", 0x10)
            return
        except Exception:
            pass
    print(message, file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(run())
