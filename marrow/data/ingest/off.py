"""Open Food Facts JSON lines / product objects → FoodRecord."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterator

from marrow.data.foods.nutrients import nutrients_from_off_nutriments
from marrow.data.ingest.models import FoodRecord, ServingRecord
from marrow.data.ingest.normalize import score_data_quality


def food_record_from_off_product(product: dict[str, Any]) -> FoodRecord | None:
    code = product.get("code") or product.get("_id")
    name = product.get("product_name") or product.get("product_name_en") or product.get("generic_name")
    if not code or not name:
        return None

    nutriments = product.get("nutriments") or {}
    nutrients = nutrients_from_off_nutriments(nutriments)
    if nutrients.macro_count() == 0:
        return None

    basis = "per_100ml" if product.get("product_quantity_unit") == "ml" else "per_100g"
    serving_size = product.get("serving_size") or product.get("serving_quantity")
    servings = [
        ServingRecord(
            label="100 g" if basis == "per_100g" else "100 ml",
            amount=100.0,
            unit="g" if basis == "per_100g" else "ml",
            grams_equivalent=100.0,
            is_default=True,
            sort_order=0,
        )
    ]
    if serving_size:
        try:
            grams = float(product.get("serving_quantity") or serving_size)
            servings.append(
                ServingRecord(
                    label=str(serving_size),
                    amount=1.0,
                    unit="serving",
                    grams_equivalent=grams,
                    is_default=False,
                    sort_order=1,
                )
            )
        except (TypeError, ValueError):
            pass

    return FoodRecord(
        source="off",
        source_food_id=str(code),
        name=str(name).strip(),
        basis=basis,
        preparation="unknown",
        data_quality=score_data_quality("off", nutrients),
        brand=product.get("brands"),
        barcode=str(code),
        locale=product.get("lang") or product.get("countries"),
        nutrients=nutrients,
        servings=servings,
    )


def load_off_jsonl(path: Path) -> list[FoodRecord]:
    records: list[FoodRecord] = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            product = json.loads(line)
            rec = food_record_from_off_product(product)
            if rec:
                records.append(rec)
    return records


def iter_off_from_fixture_dir(directory: Path) -> Iterator[FoodRecord]:
    for path in sorted(directory.glob("*.jsonl")):
        yield from load_off_jsonl(path)
