"""Rule-based natural-language food log parser (M4 local path)."""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from typing import Literal

from marrow.data.foods.units import normalize_unit

MatchConfidence = Literal["EXACT", "GOOD", "ESTIMATED"]

_WORD_NUMBERS: dict[str, float] = {
    "zero": 0,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "a": 1,
    "an": 1,
    "half": 0.5,
    "quarter": 0.25,
    # Hinglish / Hindi transliterations (common in quick logs)
    "ek": 1,
    "do": 2,
    "teen": 3,
    "char": 4,
    "aadha": 0.5,
    "adha": 0.5,
    "pauna": 0.75,
}

# Food name hints before FTS (lowercase key → search query)
HINGLISH_FOOD_ALIASES: dict[str, str] = {
    "roti": "chapati",
    "rotis": "chapati",
    "chapati": "chapati",
    "chapatis": "chapati",
    "chawal": "rice white cooked",
    "rice": "rice",
    "dal": "dal masoor",
    "daal": "dal masoor",
    "dahi": "curd",
    "doodh": "milk whole",
    "milk": "milk",
    "paneer": "paneer",
    "idli": "idli",
    "idly": "idli",
    "banana": "banana",
    "kela": "banana",
    "anda": "egg",
    "chicken": "chicken breast",
    "spinach": "spinach",
    "palak": "spinach",
}

@dataclass(frozen=True)
class ParsedSegment:
    raw: str
    amount: float
    unit: str
    food_query: str


def _parse_word_number(token: str) -> float | None:
    key = token.strip().lower()
    if key in _WORD_NUMBERS:
        return _WORD_NUMBERS[key]
    try:
        return float(key)
    except ValueError:
        return None


def parse_quantity_token(text: str) -> float | None:
    """Parse a quantity fragment (digits, fractions, or words)."""
    raw = text.strip().lower()
    if not raw:
        return None

    and_half = re.match(r"^(\d+(?:\.\d+)?)\s+and\s+(?:a\s+)?half$", raw)
    if and_half:
        return float(and_half.group(1)) + 0.5

    frac = re.match(r"^(\d+)\s+(\d+)\s*/\s*(\d+)$", raw)
    if frac:
        whole = float(frac.group(1))
        num = float(frac.group(2))
        den = float(frac.group(3))
        if den == 0:
            return None
        return whole + num / den

    frac_only = re.match(r"^(\d+)\s*/\s*(\d+)$", raw)
    if frac_only:
        num = float(frac_only.group(1))
        den = float(frac_only.group(2))
        if den == 0:
            return None
        return num / den

    if raw in _WORD_NUMBERS:
        return _WORD_NUMBERS[raw]

    try:
        return float(raw)
    except ValueError:
        return None


def _protect_compound_amounts(text: str) -> str:
    """Keep '2 and a half' intact before segment splitting."""
    return re.sub(
        r"(\d+)\s+and\s+(?:a\s+)?half",
        lambda m: str(float(m.group(1)) + 0.5),
        text,
        flags=re.IGNORECASE,
    )


def split_log_segments(text: str) -> list[str]:
    """Split a multi-item log line into single-food fragments."""
    normalized = _protect_compound_amounts(text.strip())
    if not normalized:
        return []
    parts = re.split(r"\s*(?:,|;|\+|\n)\s*|\s+\band\s+\b", normalized, flags=re.IGNORECASE)
    return [p.strip() for p in parts if p.strip()]


def _extract_amount_unit_rest(segment: str) -> tuple[float, str, str]:
    seg = segment.strip()
    if not seg:
        return 1.0, "serving", ""

    tokens = seg.split()
    if not tokens:
        return 1.0, "serving", seg

    # Try leading numeric / fraction / word number
    amount: float | None = None
    consumed = 0

    if len(tokens) >= 3 and tokens[1] == "/" and tokens[0].isdigit() and tokens[2].isdigit():
        amount = parse_quantity_token(f"{tokens[0]}/{tokens[2]}")
        consumed = 3
    elif len(tokens) >= 4 and tokens[1].isdigit() and tokens[2] == "/" and tokens[3].isdigit():
        amount = parse_quantity_token(f"{tokens[0]} {tokens[1]}/{tokens[3]}")
        consumed = 4
    else:
        joined_two = " ".join(tokens[:2]).lower()
        amount = parse_quantity_token(joined_two)
        if amount is not None and (
            joined_two in _WORD_NUMBERS or re.search(r"\band\b", joined_two)
        ):
            consumed = 2
        else:
            amount = parse_quantity_token(tokens[0])
            if amount is not None:
                consumed = 1

    if amount is None:
        return 1.0, "serving", seg

    rest_tokens = tokens[consumed:]
    if not rest_tokens:
        return amount, "serving", ""

    unit_candidate = rest_tokens[0].lower().rstrip(".")
    unit_key = re.sub(r"[^a-z0-9]", "", unit_candidate)
    norm = normalize_unit(unit_key) if unit_key else "serving"
    known_units = {
        "g",
        "kg",
        "ml",
        "l",
        "cup",
        "tbsp",
        "tsp",
        "oz",
        "piece",
        "medium",
        "roti",
        "katori",
        "bowl",
        "serving",
    }
    if norm in known_units:
        food_rest = " ".join(rest_tokens[1:])
        return amount, norm, food_rest.strip()
    food_rest = " ".join(rest_tokens)
    return amount, "serving", food_rest.strip()


def resolve_food_query(food_text: str) -> str:
    text = food_text.strip().lower()
    if not text:
        return ""
    tokens = re.findall(r"[a-z]+", text)
    if not tokens:
        return food_text.strip()
    # Prefer longest alias token in the fragment
    for tok in sorted(tokens, key=len, reverse=True):
        if tok in HINGLISH_FOOD_ALIASES:
            return HINGLISH_FOOD_ALIASES[tok]
    return food_text.strip()


def parse_segment(segment: str) -> ParsedSegment:
    amount, unit, rest = _extract_amount_unit_rest(segment)
    query = resolve_food_query(rest if rest else segment)
    if not query:
        query = resolve_food_query(segment)
    return ParsedSegment(raw=segment.strip(), amount=amount, unit=unit, food_query=query)


def new_draft_id() -> str:
    return uuid.uuid4().hex[:12]
