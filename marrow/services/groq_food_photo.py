"""Groq vision — meal photo → structured food suggestions (ESTIMATED, confirm in UI)."""

from __future__ import annotations

import base64
import logging
import re
import sqlite3
from typing import Any

from marrow.core.groq_settings import groq_configured, load_groq_settings
from marrow.services.groq_client import GroqClient, GroqClientError, default_client
from marrow.services.groq_food_parse import groq_items_to_drafts, validate_groq_items, _parse_json_content

log = logging.getLogger(__name__)

PHOTO_SYSTEM = """You describe visible foods on a plate for nutrition logging. Rules:
- Output ONLY valid JSON.
- Never include calories, macros, or nutrient numbers.
- Estimate reasonable portions with household units.
Schema:
{"items":[{"food_name":str,"quantity":number,"unit":str,"meal":str,"dish":bool,"ingredients":[{"food_name":str,"grams":number}]}]}
Meal must be one of: breakfast, lunch, dinner, snack, pre_workout, post_workout."""


def _normalize_image_payload(image_base64: str, mime_type: str) -> tuple[str, str]:
    raw = image_base64.strip()
    if raw.startswith("data:"):
        match = re.match(r"data:([^;]+);base64,(.+)", raw, re.DOTALL)
        if match:
            return match.group(2).strip(), match.group(1)
    clean = re.sub(r"\s+", "", raw)
    mime = (mime_type or "image/jpeg").strip() or "image/jpeg"
    return clean, mime


def parse_food_photo_with_groq(
    conn: sqlite3.Connection,
    image_base64: str,
    *,
    mime_type: str = "image/jpeg",
    meal_tag: str = "snack",
    client: GroqClient | None = None,
) -> list[dict[str, Any]]:
    settings = load_groq_settings()
    if not settings.get("enable_photo_parse", True):
        return []
    if not groq_configured():
        return []
    groq = client or default_client()
    if not groq.available:
        return []

    b64, mime = _normalize_image_payload(image_base64, mime_type)
    try:
        base64.b64decode(b64, validate=True)
    except Exception:
        raise ValueError("Invalid image payload") from None

    data_url = f"data:{mime};base64,{b64}"
    messages = [
        {"role": "system", "content": PHOTO_SYSTEM},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "List each distinct food item you can see with estimated portions."},
                {"type": "image_url", "image_url": {"url": data_url}},
            ],
        },
    ]
    try:
        raw = groq.chat_completion(
            messages,
            temperature=0.0,
            response_format={"type": "json_object"},
            vision=True,
        )
    except GroqClientError as exc:
        log.warning("Groq photo parse failed: %s", exc)
        return []

    try:
        payload = _parse_json_content(raw)
        groq_items = validate_groq_items(payload, meal_tag)
    except (ValueError, TypeError) as exc:
        log.warning("Groq photo JSON invalid: %s", exc)
        return []

    drafts = groq_items_to_drafts(conn, groq_items, source_text="[meal photo]")
    for draft in drafts:
        draft["match_confidence"] = "ESTIMATED"
        draft["raw_fragment"] = f"[photo] {draft.get('raw_fragment', draft.get('food_query', ''))}"
        warnings = list(draft.get("warnings") or [])
        if "photo_estimate" not in warnings:
            warnings.append("photo_estimate")
        draft["warnings"] = warnings
    return drafts


def parse_food_photo(
    conn: sqlite3.Connection,
    image_base64: str,
    *,
    mime_type: str = "image/jpeg",
    meal_tag: str = "snack",
) -> dict[str, Any]:
    drafts = parse_food_photo_with_groq(conn, image_base64, mime_type=mime_type, meal_tag=meal_tag)
    resolved_meal = meal_tag
    for draft in drafts:
        tag = draft.pop("_meal_tag", None)
        if isinstance(tag, str):
            resolved_meal = tag
    return {
        "meal_tag": resolved_meal,
        "items": drafts,
        "parser": "groq_photo" if drafts else "none",
        "groq_available": groq_configured(),
        "groq_used": bool(drafts),
        "source": "photo",
    }
