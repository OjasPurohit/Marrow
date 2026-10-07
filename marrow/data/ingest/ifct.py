"""IFCT-style CSV (Indian Food Composition Tables) → FoodRecord."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterator

from marrow.data.foods.nutrients import nutrients_from_ifct_row
from marrow.data.ingest.models import FoodRecord, ServingRecord
from marrow.data.ingest.normalize import score_data_quality


def food_record_from_ifct_row(row: dict[str, str]) -> FoodRecord | None:
    code = row.get("food_code", "").strip()
    name = row.get("food_name", "").strip()
    if not code or not name:
        return None

    nutrients = nutrients_from_ifct_row(row)
    preparation = row.get("preparation", "unknown").strip().lower() or "unknown"
    if preparation not in ("raw", "cooked", "unknown"):
        preparation = "unknown"

    return FoodRecord(
        source="ifct",
        source_food_id=code,
        name=name,
        basis="per_100g",
        preparation=preparation,
        data_quality=score_data_quality("ifct", nutrients),
        locale="en-IN",
        nutrients=nutrients,
        servings=[
            ServingRecord(
                label="100 g",
                amount=100.0,
                unit="g",
                grams_equivalent=100.0,
                is_default=True,
            )
        ],
    )


def load_ifct_csv(path: Path) -> list[FoodRecord]:
    records: list[FoodRecord] = []
    with path.open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            rec = food_record_from_ifct_row(row)
            if rec:
                records.append(rec)
    return records


def iter_ifct_from_fixture_dir(directory: Path) -> Iterator[FoodRecord]:
    for path in sorted(directory.glob("*.csv")):
        yield from load_ifct_csv(path)
