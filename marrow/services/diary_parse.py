"""Parse natural-language food logs and build confirmation drafts."""

from __future__ import annotations

import os
import re
import sqlite3
from typing import Literal

from marrow.services.food_detail import convert_food_serving
from marrow.services.food_search import search_foods
from marrow.services.food_text_parser import (
    MatchConfidence,
    new_draft_id,
    parse_segment,
    split_log_segments,
)
from marrow.services.nutrient_validation import collect_nutrient_warnings, nutrients_for_display

ParserStage = Literal["local", "groq", "none"]


def groq_parser_configured() -> bool:
    key = os.environ.get("GROQ_API_KEY", "").strip()
    return bool(key)


def _name_match_confidence(query: str, food_name: str, rank: float) -> MatchConfidence:
    q = re.sub(r"[^a-z0-9\s]", " ", query.lower())
    name = food_name.lower()
    q_tokens = [t for t in q.split() if len(t) > 2]
    if not q_tokens:
        return "ESTIMATED"
    if all(tok in name for tok in q_tokens):
        return "EXACT"
    if rank <= -1.0:
        return "GOOD"
    return "ESTIMATED"


def _build_draft_item(
    conn: sqlite3.Connection,
    segment_raw: str,
    amount: float,
    unit: str,
    food_query: str,
    search_hit: dict | None,
) -> dict:
    draft_id = new_draft_id()
    if not search_hit:
        return {
            "draft_id": draft_id,
            "raw_fragment": segment_raw,
            "amount": amount,
            "unit": unit,
            "food_query": food_query,
            "food_id": None,
            "food_name": None,
            "match_confidence": "ESTIMATED",
            "energy_kcal": None,
            "nutrients": {},
            "grams_equivalent": None,
            "warnings": ["no_food_match"],
            "conversion_note": None,
        }

    food_id = int(search_hit["id"])
    confidence = _name_match_confidence(
        food_query,
        str(search_hit["name"]),
        float(search_hit.get("rank", 0.0)),
    )
    try:
        converted = convert_food_serving(conn, food_id, amount, unit)
    except ValueError as exc:
        return {
            "draft_id": draft_id,
            "raw_fragment": segment_raw,
            "amount": amount,
            "unit": unit,
            "food_query": food_query,
            "food_id": food_id,
            "food_name": search_hit["name"],
            "match_confidence": confidence,
            "energy_kcal": None,
            "nutrients": {},
            "grams_equivalent": None,
            "warnings": ["invalid_portion", str(exc)],
            "conversion_note": None,
        }

    nutrients = nutrients_for_display(converted["nutrients"])
    energy = nutrients.get("energy_kcal")
    warnings = collect_nutrient_warnings(
        energy_kcal=energy,
        protein_g=nutrients.get("protein_g"),
        carbs_g=nutrients.get("carbs_g"),
        fat_g=nutrients.get("fat_g"),
        grams_equivalent=float(converted["grams_equivalent"]),
        serving_note=converted.get("note"),
    )
    if confidence == "ESTIMATED" and "estimated_serving" not in warnings:
        if converted.get("note"):
            warnings.append("estimated_serving")

    return {
        "draft_id": draft_id,
        "raw_fragment": segment_raw,
        "amount": float(converted["amount"]),
        "unit": converted["unit"],
        "food_query": food_query,
        "food_id": food_id,
        "food_name": search_hit["name"],
        "match_confidence": confidence,
        "energy_kcal": energy,
        "nutrients": nutrients,
        "grams_equivalent": float(converted["grams_equivalent"]),
        "warnings": warnings,
        "conversion_note": converted.get("note"),
        "alternatives": [],
    }


def parse_food_text(
    conn: sqlite3.Connection,
    text: str,
    *,
    meal_tag: str = "snack",
) -> dict:
    """Local rule-based parser with optional Groq stage (inactive without API key)."""
    segments = split_log_segments(text)
    items: list[dict] = []

    for segment in segments:
        parsed = parse_segment(segment)
        search = search_foods(conn, parsed.food_query, limit=5)
        results = search.get("results") or []
        hit = results[0] if results else None
        item = _build_draft_item(
            conn,
            parsed.raw,
            parsed.amount,
            parsed.unit,
            parsed.food_query,
            hit,
        )
        if len(results) > 1:
            item["alternatives"] = [
                {"id": r["id"], "name": r["name"], "rank": r.get("rank")}
                for r in results[1:5]
            ]
        items.append(item)

    parser_used: ParserStage = "local"
    groq_available = groq_parser_configured()

    # Reserved Groq slot (M8): only runs when key present and local found nothing.
    if groq_available and text.strip() and all(i.get("food_id") is None for i in items):
        parser_used = "groq"
        # M8 will call Groq here; keep pipeline hook without network in M4.
        pass

    return {
        "input": text,
        "meal_tag": meal_tag,
        "items": items,
        "parser": parser_used,
        "groq_available": groq_available,
        "groq_used": False,
    }
