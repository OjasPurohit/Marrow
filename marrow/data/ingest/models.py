"""In-memory records produced by source parsers before catalog write."""

from __future__ import annotations

from dataclasses import dataclass, field

from marrow.data.foods.nutrients import NutrientValues


@dataclass
class ServingRecord:
    label: str
    amount: float
    unit: str
    grams_equivalent: float
    is_default: bool = False
    sort_order: int = 0


@dataclass
class FoodRecord:
    source: str
    source_food_id: str
    name: str
    basis: str = "per_100g"
    preparation: str = "unknown"
    data_quality: str = "medium"
    brand: str | None = None
    barcode: str | None = None
    locale: str | None = None
    nutrients: NutrientValues = field(default_factory=NutrientValues)
    servings: list[ServingRecord] = field(default_factory=list)
