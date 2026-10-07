"""Optional Groq narrative for night review (facts from computed totals only)."""

from __future__ import annotations

import json
import logging
from typing import Any

from marrow.core.groq_settings import groq_configured, load_groq_settings
from marrow.services.groq_client import GroqClient, GroqClientError, default_client

log = logging.getLogger(__name__)

SUMMARY_SYSTEM = """You write a short, friendly night-review recap (2-4 sentences).
Use ONLY the numeric facts provided in the user message.
Do NOT invent or estimate any nutrient values, calories, or percentages.
If data is missing, say so briefly. No bullet lists."""


def build_facts_payload(
    energy_balance: dict[str, Any],
    macro_totals: dict[str, float | None],
    summary_lines: list[str],
    flagged: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "energy_balance": energy_balance,
        "macro_totals": {k: macro_totals.get(k) for k in ("energy_kcal", "protein_g", "carbs_g", "fat_g")},
        "rule_summary_lines": summary_lines,
        "flagged_nutrients": [
            {
                "label": row.get("label"),
                "flag": row.get("flag"),
                "pct_of_target": row.get("pct_of_target"),
            }
            for row in flagged[:8]
        ],
    }


def maybe_groq_night_summary(
    energy_balance: dict[str, Any],
    macro_totals: dict[str, float | None],
    summary_lines: list[str],
    flagged: list[dict[str, Any]],
    *,
    client: GroqClient | None = None,
) -> str | None:
    settings = load_groq_settings()
    if not settings.get("enable_night_summary", True):
        return None
    if not groq_configured():
        return None
    groq = client or default_client()
    if not groq.available:
        return None
    facts = build_facts_payload(energy_balance, macro_totals, summary_lines, flagged)
    user = json.dumps(facts, indent=2)
    try:
        text = groq.chat_completion(
            [
                {"role": "system", "content": SUMMARY_SYSTEM},
                {"role": "user", "content": user},
            ],
            temperature=0.0,
        )
        clean = text.strip()
        return clean or None
    except GroqClientError as exc:
        log.info("Groq night summary skipped: %s", exc)
        return None
