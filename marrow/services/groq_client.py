"""Minimal Groq HTTP client (chat + Whisper) with timeouts and retry on rate limits."""

from __future__ import annotations

import json
import logging
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable

from marrow.core.groq_settings import (
    DEFAULT_GROQ_SETTINGS,
    load_groq_settings,
    resolve_groq_api_key_for_runtime,
)

log = logging.getLogger(__name__)

GROQ_API_BASE = "https://api.groq.com/openai/v1"

TransportFn = Callable[..., Any]


@dataclass
class GroqClientError(Exception):
    message: str
    status: int | None = None
    retryable: bool = False

    def __str__(self) -> str:
        return self.message


class GroqClient:
    def __init__(
        self,
        api_key: str | None = None,
        *,
        transport: TransportFn | None = None,
        settings: dict[str, Any] | None = None,
    ) -> None:
        self._api_key = api_key or resolve_groq_api_key_for_runtime()
        base = load_groq_settings()
        if settings:
            base = {**base, **settings}
        self._settings = {**DEFAULT_GROQ_SETTINGS, **base}
        self._transport = transport or self._default_transport

    @property
    def available(self) -> bool:
        return bool(self._api_key)

    def chat_completion(
        self,
        messages: list[dict[str, str]],
        *,
        model: str | None = None,
        temperature: float = 0.0,
        response_format: dict[str, str] | None = None,
    ) -> str:
        if not self._api_key:
            raise GroqClientError("Groq API key not configured", retryable=False)
        body: dict[str, Any] = {
            "model": model or self._settings["chat_model"],
            "messages": messages,
            "temperature": temperature,
        }
        if response_format:
            body["response_format"] = response_format
        data = self._request_json(
            "POST",
            "/chat/completions",
            body,
        )
        try:
            return str(data["choices"][0]["message"]["content"])
        except (KeyError, IndexError, TypeError) as exc:
            raise GroqClientError("Unexpected Groq chat response shape") from exc

    def transcribe_audio(self, audio_bytes: bytes, *, filename: str = "audio.wav") -> str:
        if not self._api_key:
            raise GroqClientError("Groq API key not configured", retryable=False)
        if not audio_bytes:
            raise GroqClientError("Empty audio payload", retryable=False)
        model = self._settings["whisper_model"]
        timeout = float(self._settings["request_timeout_sec"])
        url = f"{GROQ_API_BASE}/audio/transcriptions"
        boundary = "----marrowgroqboundary"
        parts: list[bytes] = []
        for name, value in (("model", model), ("temperature", "0")):
            parts.append(f"--{boundary}\r\n".encode())
            parts.append(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode())
            parts.append(value.encode())
            parts.append(b"\r\n")
        parts.append(f"--{boundary}\r\n".encode())
        parts.append(
            f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'.encode()
        )
        parts.append(b"Content-Type: audio/wav\r\n\r\n")
        parts.append(audio_bytes)
        parts.append(b"\r\n")
        parts.append(f"--{boundary}--\r\n".encode())
        payload = b"".join(parts)
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        }
        req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
        data = self._send_with_retries(req, timeout=timeout)
        try:
            return str(data["text"]).strip()
        except (KeyError, TypeError) as exc:
            raise GroqClientError("Unexpected Groq transcription response") from exc

    def _request_json(self, method: str, path: str, body: dict[str, Any]) -> dict[str, Any]:
        timeout = float(self._settings["request_timeout_sec"])
        url = f"{GROQ_API_BASE}{path}"
        payload = json.dumps(body).encode("utf-8")
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        req = urllib.request.Request(url, data=payload, headers=headers, method=method)
        return self._send_with_retries(req, timeout=timeout)

    def _send_with_retries(self, req: urllib.request.Request, *, timeout: float) -> dict[str, Any]:
        max_retries = int(self._settings.get("max_retries", 2))
        delay = 0.5
        last_error: GroqClientError | None = None
        for attempt in range(max_retries + 1):
            try:
                return self._transport(req, timeout=timeout)
            except GroqClientError as exc:
                last_error = exc
                if not exc.retryable or attempt >= max_retries:
                    raise
                time.sleep(delay)
                delay = min(delay * 2, 4.0)
        assert last_error is not None
        raise last_error

    def _default_transport(self, req: urllib.request.Request, *, timeout: float) -> dict[str, Any]:
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            retryable = exc.code in (429, 500, 502, 503, 504)
            detail = exc.read().decode("utf-8", errors="replace")[:500]
            raise GroqClientError(
                f"Groq HTTP {exc.code}: {detail}",
                status=exc.code,
                retryable=retryable,
            ) from exc
        except urllib.error.URLError as exc:
            raise GroqClientError(f"Groq network error: {exc.reason}", retryable=True) from exc
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise GroqClientError("Invalid JSON from Groq") from exc


def default_client() -> GroqClient:
    return GroqClient()
