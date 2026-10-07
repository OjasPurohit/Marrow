"""Shared normalization helpers for food ingestion."""

from __future__ import annotations

import re
import unicodedata

from marrow.data.foods.nutrients import NutrientValues

_WHITESPACE = re.compile(r"\s+")
_NON_ALNUM = re.compile(r"[^a-z0-9]+")


def normalize_food_name(name: str) -> str:
    """Lowercase, strip accents, collapse punctuation for search keys."""
    text = unicodedata.normalize("NFKD", name)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower().strip()
    text = _WHITESPACE.sub(" ", text)
    return text


def slug_for_search(name: str) -> str:
    base = normalize_food_name(name)
    base = _NON_ALNUM.sub(" ", base)
    return _WHITESPACE.sub(" ", base).strip()


def infer_preparation(description: str | None, food_category: str | None = None) -> str:
    blob = " ".join(filter(None, [description, food_category])).lower()
    if any(k in blob for k in ("cooked", "boiled", "fried", "roasted", "baked", "steamed")):
        return "cooked"
    if any(k in blob for k in ("raw", "fresh", "uncooked")):
        return "raw"
    return "unknown"


def score_data_quality(source: str, nutrients: NutrientValues, *, branded: bool = False) -> str:
    macros = nutrients.macro_count()
    micros = nutrients.non_null_count() - macros
    if source == "usda" and not branded and macros >= 4 and micros >= 8:
        return "high"
    if source == "ifct" and macros >= 3:
        return "high"
    if source == "off":
        if macros >= 4 and nutrients.energy_kcal is not None:
            return "medium"
        return "low"
    if macros >= 3:
        return "medium"
    if macros >= 1:
        return "estimated"
    return "low"


def parse_float(value: object | None) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if not text or text in ("-", "NA", "Tr", "tr"):
        return None
    try:
        return float(text)
    except ValueError:
        return None
