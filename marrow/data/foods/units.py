"""Serving-size conversion to grams (or ml for per_100ml foods)."""

from __future__ import annotations

import re
from dataclasses import dataclass

# Canonical unit aliases → internal key
UNIT_ALIASES: dict[str, str] = {
    "g": "g",
    "gram": "g",
    "grams": "g",
    "kg": "kg",
    "kilogram": "kg",
    "ml": "ml",
    "milliliter": "ml",
    "millilitre": "ml",
    "l": "l",
    "liter": "l",
    "litre": "l",
    "cup": "cup",
    "cups": "cup",
    "tbsp": "tbsp",
    "tablespoon": "tbsp",
    "tablespoons": "tbsp",
    "tsp": "tsp",
    "teaspoon": "tsp",
    "teaspoons": "tsp",
    "oz": "oz",
    "ounce": "oz",
    "ounces": "oz",
    "piece": "piece",
    "pieces": "piece",
    "pc": "piece",
    "medium": "medium",
    "roti": "roti",
    "rotis": "roti",
    "katori": "katori",
    "bowl": "bowl",
    "serving": "serving",
}

# Mass/volume → grams (water-density defaults for volume; per_100ml uses ml path).
MASS_TO_GRAMS: dict[str, float] = {
    "g": 1.0,
    "kg": 1000.0,
    "oz": 28.3495,
}

VOLUME_TO_ML: dict[str, float] = {
    "ml": 1.0,
    "l": 1000.0,
    "cup": 240.0,
    "tbsp": 15.0,
    "tsp": 5.0,
}

# Typical Indian / household portions when food has no custom serving row (grams).
DEFAULT_PIECE_GRAMS: dict[str, float] = {
    "piece": 50.0,
    "medium": 118.0,
    "roti": 40.0,
    "katori": 150.0,
    "bowl": 200.0,
    "serving": 100.0,
}

# Cooked vs raw weight change (multiply raw grams to get cooked equivalent mass).
# Values are approximate yield factors for staples when swapping preparation.
RAW_TO_COOKED_FACTOR: dict[str, float] = {
    "rice": 2.8,
    "chicken": 0.75,
    "spinach": 0.25,
}

COOKED_TO_RAW_FACTOR: dict[str, float] = {
    k: 1.0 / v for k, v in RAW_TO_COOKED_FACTOR.items()
}


@dataclass(frozen=True)
class ServingConversion:
    amount: float
    unit: str
    grams_equivalent: float
    basis_amount: float
    basis: str
    matched_food_serving: bool
    note: str | None = None


def normalize_unit(unit: str) -> str:
    key = unit.strip().lower()
    key = re.sub(r"[^a-z0-9]", "", key)
    return UNIT_ALIASES.get(key, key)


def _food_staple_key(name: str) -> str | None:
    lower = name.lower()
    for staple in RAW_TO_COOKED_FACTOR:
        if staple in lower:
            return staple
    return None


def preparation_adjustment_factor(
    food_name: str,
    from_preparation: str,
    to_preparation: str,
) -> float:
    """Scale grams when converting between raw and cooked for known staples."""
    if from_preparation == to_preparation:
        return 1.0
    staple = _food_staple_key(food_name)
    if not staple:
        return 1.0
    if from_preparation == "raw" and to_preparation == "cooked":
        return RAW_TO_COOKED_FACTOR[staple]
    if from_preparation == "cooked" and to_preparation == "raw":
        return COOKED_TO_RAW_FACTOR[staple]
    return 1.0


def convert_to_basis_amount(
    amount: float,
    unit: str,
    *,
    basis: str,
    food_name: str,
    preparation: str,
    food_servings: list[dict[str, float | str | int | bool]] | None = None,
    target_preparation: str | None = None,
) -> ServingConversion:
    """
    Convert a user portion to grams (per_100g) or ml (per_100ml).
    Uses food-specific servings when unit/amount match a catalog row.
    """
    if amount <= 0:
        raise ValueError("amount must be positive")

    norm = normalize_unit(unit)
    target_prep = target_preparation or preparation

    matched = False
    grams_eq: float | None = None

    if food_servings:
        for row in food_servings:
            row_unit = normalize_unit(str(row["unit"]))
            row_amount = float(row["amount"])
            if row_unit == norm and abs(row_amount - amount) < 1e-6:
                grams_eq = float(row["grams_equivalent"])
                matched = True
                break
            if norm == "serving" and row.get("is_default"):
                scale = amount / row_amount if row_amount else amount
                grams_eq = float(row["grams_equivalent"]) * scale
                matched = True
                break

    note: str | None = None
    if grams_eq is None:
        if norm in MASS_TO_GRAMS:
            grams_eq = amount * MASS_TO_GRAMS[norm]
        elif norm in VOLUME_TO_ML:
            ml = amount * VOLUME_TO_ML[norm]
            if basis == "per_100ml":
                grams_eq = ml
            else:
                grams_eq = ml
                note = "volume_assumed_water_density"
        elif norm in DEFAULT_PIECE_GRAMS:
            grams_eq = amount * DEFAULT_PIECE_GRAMS[norm]
            note = "default_piece_weight"
        else:
            raise ValueError(f"unknown unit: {unit}")

    factor = preparation_adjustment_factor(food_name, preparation, target_prep)
    grams_eq *= factor

    basis_amount = grams_eq if basis == "per_100ml" else grams_eq

    return ServingConversion(
        amount=amount,
        unit=norm,
        grams_equivalent=grams_eq,
        basis_amount=basis_amount,
        basis=basis,
        matched_food_serving=matched,
        note=note,
    )


def scale_nutrients(
    per_100: dict[str, float | None],
    basis_amount: float,
    basis: str = "per_100g",
) -> dict[str, float | None]:
    """Scale per-100g/ml nutrient columns to the given basis amount."""
    divisor = 100.0
    factor = basis_amount / divisor
    out: dict[str, float | None] = {}
    for key, value in per_100.items():
        if value is None:
            out[key] = None
        else:
            out[key] = round(float(value) * factor, 4)
    return out
