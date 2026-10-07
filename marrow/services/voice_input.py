"""Voice capture + Groq Whisper transcription (optional desktop hotkey)."""

from __future__ import annotations

import io
import logging
import threading
import wave
from typing import Callable

from marrow.core.groq_settings import groq_configured, load_groq_settings
from marrow.services.groq_client import GroqClient, GroqClientError, default_client

log = logging.getLogger(__name__)

_last_transcript: str | None = None
_last_error: str | None = None
_listener_started = False


def get_last_voice_transcript(clear: bool = False) -> dict:
    global _last_transcript, _last_error
    payload = {
        "text": _last_transcript,
        "error": _last_error,
        "configured": groq_configured(),
    }
    if clear:
        _last_transcript = None
        _last_error = None
    return payload


def _record_wav_bytes(duration_sec: float, sample_rate: int = 16_000) -> bytes:
    try:
        import sounddevice as sd  # type: ignore[import-untyped]
    except ImportError as exc:
        raise RuntimeError(
            "Voice capture requires the sounddevice package (pip install sounddevice)"
        ) from exc

    frames = int(duration_sec * sample_rate)
    audio = sd.rec(frames, samplerate=sample_rate, channels=1, dtype="int16")
    sd.wait()
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(audio.tobytes())
    return buffer.getvalue()


def transcribe_wav_bytes(
    audio_bytes: bytes,
    *,
    client: GroqClient | None = None,
) -> str:
    groq = client or default_client()
    return groq.transcribe_audio(audio_bytes, filename="marrow-voice.wav")


def capture_and_transcribe(
    duration_sec: float | None = None,
    *,
    client: GroqClient | None = None,
) -> str:
    if not groq_configured():
        raise RuntimeError("Groq API key not configured")
    settings = load_groq_settings()
    seconds = float(duration_sec or settings.get("voice_record_seconds", 8.0))
    audio = _record_wav_bytes(seconds)
    return transcribe_wav_bytes(audio, client=client)


def _run_hotkey_cycle(on_text: Callable[[str], None] | None = None) -> None:
    global _last_transcript, _last_error
    try:
        text = capture_and_transcribe()
        _last_transcript = text
        _last_error = None
        if on_text:
            on_text(text)
    except Exception as exc:  # noqa: BLE001 — surface to UI polling
        _last_error = str(exc)
        log.warning("Voice hotkey failed: %s", exc)


def start_voice_hotkey_listener(on_text: Callable[[str], None] | None = None) -> bool:
    """Register global hotkey once (no-op when Groq/voice disabled or deps missing)."""
    global _listener_started
    settings = load_groq_settings()
    if not settings.get("enable_voice_hotkey", True):
        return False
    if not groq_configured():
        return False
    if _listener_started:
        return True

    hotkey = str(settings.get("voice_hotkey") or "ctrl+shift+v").lower()

    try:
        from pynput import keyboard  # type: ignore[import-untyped]
    except ImportError:
        log.info("pynput not installed; voice hotkey disabled")
        return False

    pressed: set[str] = set()

    def normalize(key) -> str | None:
        if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
            return "ctrl"
        if key == keyboard.Key.shift_l or key == keyboard.Key.shift_r:
            return "shift"
        if key == keyboard.Key.alt_l or key == keyboard.Key.alt_r:
            return "alt"
        if hasattr(key, "char") and key.char:
            return key.char.lower()
        return None

    required = set(hotkey.split("+"))

    def on_press(key):
        name = normalize(key)
        if name:
            pressed.add(name)
        if required.issubset(pressed):
            threading.Thread(
                target=_run_hotkey_cycle,
                args=(on_text,),
                daemon=True,
            ).start()

    def on_release(key):
        name = normalize(key)
        if name and name in pressed:
            pressed.discard(name)

    listener = keyboard.Listener(on_press=on_press, on_release=on_release)
    listener.daemon = True
    listener.start()
    _listener_started = True
    log.info("Voice hotkey listener started (%s)", hotkey)
    return True
