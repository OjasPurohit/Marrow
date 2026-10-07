"""USDA FoodData Central JSON → FoodRecord."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterator

from marrow.data.foods.nutrients import nutrients_from_usda_entries
from marrow.data.ingest.models import FoodRecord, ServingRecord
from marrow.data.ingest.normalize import infer_preparation, score_data_quality


def _default_serving(description: str | None) -> list[ServingRecord]:
    return [
        ServingRecord(
            label="100 g",
            amount=100.0,
            unit="g",
            grams_equivalent=100.0,
            is_default=True,
            sort_order=0,
        )
    ]


def food_record_from_usda_item(item: dict[str, Any]) -> FoodRecord | None:
    fdc_id = item.get("fdcId") or item.get("fdc_id")
    description = item.get("description") or item.get("foodDescription")
    if fdc_id is None or not description:
        return None

    data_type = (item.get("dataType") or item.get("data_type") or "").lower()
    branded = data_type == "branded_food" or "brandOwner" in item

    nutrients_raw = item.get("foodNutrients") or item.get("nutrients") or []
    nutrients = nutrients_from_usda_entries(nutrients_raw)

    preparation = infer_preparation(description, item.get("foodCategory"))
    quality = score_data_quality("usda", nutrients, branded=branded)

    servings = _default_serving(description)
    for portion in item.get("foodPortions") or []:
        gram_weight = portion.get("gramWeight")
        if gram_weight is None:
            continue
        label = portion.get("portionDescription") or portion.get("modifier") or "Serving"
        servings.append(
            ServingRecord(
                label=str(label).strip(),
                amount=float(portion.get("amount") or 1.0),
                unit=str(portion.get("measureUnit", {}).get("name") or "serving"),
                grams_equivalent=float(gram_weight),
                is_default=False,
                sort_order=len(servings),
            )
        )

    return FoodRecord(
        source="usda",
        source_food_id=str(fdc_id),
        name=str(description).strip(),
        basis="per_100g",
        preparation=preparation,
        data_quality=quality,
        brand=item.get("brandOwner") or item.get("brandName"),
        barcode=item.get("gtinUpc"),
        locale="en",
        nutrients=nutrients,
        servings=servings,
    )


def parse_usda_json_document(data: dict[str, Any]) -> list[FoodRecord]:
    foods = data.get("FoundationFoods") or data.get("SRLegacyFoods") or data.get("foods") or []
    if isinstance(foods, dict):
        foods = list(foods.values())
    records: list[FoodRecord] = []
    for item in foods:
        rec = food_record_from_usda_item(item)
        if rec:
            records.append(rec)
    return records


def load_usda_json_path(path: Path) -> list[FoodRecord]:
    with path.open(encoding="utf-8") as fh:
        data = json.load(fh)
    return parse_usda_json_document(data)


def iter_usda_from_fixture_dir(directory: Path) -> Iterator[FoodRecord]:
    for path in sorted(directory.glob("*.json")):
        yield from load_usda_json_path(path)
