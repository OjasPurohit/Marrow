"""Canonical per-100g / per-100ml nutrient columns (NULL when unknown)."""

from __future__ import annotations

from dataclasses import dataclass, fields
from typing import Any, Iterator

# (sql_column, unit) — order matches migration 002 food_nutrients columns.
NUTRIENT_FIELDS: tuple[tuple[str, str], ...] = (
    ("energy_kcal", "kcal"),
    ("protein_g", "g"),
    ("carbs_g", "g"),
    ("fat_g", "g"),
    ("fiber_g", "g"),
    ("sugar_g", "g"),
    ("saturated_fat_g", "g"),
    ("trans_fat_g", "g"),
    ("monounsaturated_fat_g", "g"),
    ("polyunsaturated_fat_g", "g"),
    ("cholesterol_mg", "mg"),
    ("sodium_mg", "mg"),
    ("potassium_mg", "mg"),
    ("calcium_mg", "mg"),
    ("iron_mg", "mg"),
    ("magnesium_mg", "mg"),
    ("phosphorus_mg", "mg"),
    ("zinc_mg", "mg"),
    ("copper_mg", "mg"),
    ("manganese_mg", "mg"),
    ("selenium_ug", "µg"),
    ("vitamin_a_ug", "µg"),
    ("vitamin_c_mg", "mg"),
    ("vitamin_d_ug", "µg"),
    ("vitamin_e_mg", "mg"),
    ("vitamin_k_ug", "µg"),
    ("thiamin_mg", "mg"),
    ("riboflavin_mg", "mg"),
    ("niacin_mg", "mg"),
    ("vitamin_b6_mg", "mg"),
    ("folate_ug", "µg"),
    ("vitamin_b12_ug", "µg"),
    ("water_g", "g"),
    ("alcohol_g", "g"),
)

NUTRIENT_COLUMN_NAMES: tuple[str, ...] = tuple(col for col, _ in NUTRIENT_FIELDS)

# USDA FoodData Central nutrient.id → marrow column
USDA_NUTRIENT_ID_MAP: dict[int, str] = {
    1008: "energy_kcal",
    1003: "protein_g",
    1005: "carbs_g",
    1004: "fat_g",
    1079: "fiber_g",
    2000: "sugar_g",
    1258: "saturated_fat_g",
    1257: "trans_fat_g",
    1292: "monounsaturated_fat_g",
    1293: "polyunsaturated_fat_g",
    1253: "cholesterol_mg",
    1093: "sodium_mg",
    1092: "potassium_mg",
    1087: "calcium_mg",
    1089: "iron_mg",
    1090: "magnesium_mg",
    1091: "phosphorus_mg",
    1095: "zinc_mg",
    1098: "copper_mg",
    1101: "manganese_mg",
    1103: "selenium_ug",
    1106: "vitamin_a_ug",
    1162: "vitamin_c_mg",
    1114: "vitamin_d_ug",
    1109: "vitamin_e_mg",
    1185: "vitamin_k_ug",
    1165: "thiamin_mg",
    1166: "riboflavin_mg",
    1167: "niacin_mg",
    1175: "vitamin_b6_mg",
    1177: "folate_ug",
    1178: "vitamin_b12_ug",
    1051: "water_g",
    1018: "alcohol_g",
}

# Open Food Facts nutriments keys (per 100g) → marrow column
OFF_NUTRIMENT_MAP: dict[str, str] = {
    "energy-kcal": "energy_kcal",
    "energy-kcal_100g": "energy_kcal",
    "energy-kcal_value": "energy_kcal",
    "proteins": "protein_g",
    "proteins_100g": "protein_g",
    "carbohydrates": "carbs_g",
    "carbohydrates_100g": "carbs_g",
    "fat": "fat_g",
    "fat_100g": "fat_g",
    "fiber": "fiber_g",
    "fiber_100g": "fiber_g",
    "sugars": "sugar_g",
    "sugars_100g": "sugar_g",
    "saturated-fat": "saturated_fat_g",
    "saturated-fat_100g": "saturated_fat_g",
    "trans-fat": "trans_fat_g",
    "trans-fat_100g": "trans_fat_g",
    "monounsaturated-fat": "monounsaturated_fat_g",
    "monounsaturated-fat_100g": "monounsaturated_fat_g",
    "polyunsaturated-fat": "polyunsaturated_fat_g",
    "polyunsaturated-fat_100g": "polyunsaturated_fat_g",
    "cholesterol": "cholesterol_mg",
    "cholesterol_100g": "cholesterol_mg",
    "sodium": "sodium_mg",
    "sodium_100g": "sodium_mg",
    "potassium": "potassium_mg",
    "potassium_100g": "potassium_mg",
    "calcium": "calcium_mg",
    "calcium_100g": "calcium_mg",
    "iron": "iron_mg",
    "iron_100g": "iron_mg",
    "magnesium": "magnesium_mg",
    "magnesium_100g": "magnesium_mg",
    "phosphorus": "phosphorus_mg",
    "phosphorus_100g": "phosphorus_mg",
    "zinc": "zinc_mg",
    "zinc_100g": "zinc_mg",
    "copper": "copper_mg",
    "copper_100g": "copper_mg",
    "manganese": "manganese_mg",
    "manganese_100g": "manganese_mg",
    "selenium": "selenium_ug",
    "selenium_100g": "selenium_ug",
    "vitamin-a": "vitamin_a_ug",
    "vitamin-a_100g": "vitamin_a_ug",
    "vitamin-c": "vitamin_c_mg",
    "vitamin-c_100g": "vitamin_c_mg",
    "vitamin-d": "vitamin_d_ug",
    "vitamin-d_100g": "vitamin_d_ug",
    "vitamin-e": "vitamin_e_mg",
    "vitamin-e_100g": "vitamin_e_mg",
    "vitamin-k": "vitamin_k_ug",
    "vitamin-k_100g": "vitamin_k_ug",
    "vitamin-b1": "thiamin_mg",
    "vitamin-b1_100g": "thiamin_mg",
    "vitamin-b2": "riboflavin_mg",
    "vitamin-b2_100g": "riboflavin_mg",
    "vitamin-pp": "niacin_mg",
    "vitamin-pp_100g": "niacin_mg",
    "vitamin-b6": "vitamin_b6_mg",
    "vitamin-b6_100g": "vitamin_b6_mg",
    "folates": "folate_ug",
    "folates_100g": "folate_ug",
    "vitamin-b12": "vitamin_b12_ug",
    "vitamin-b12_100g": "vitamin_b12_ug",
}


@dataclass
class NutrientValues:
    """Sparse nutrient map; unset fields remain None."""

    energy_kcal: float | None = None
    protein_g: float | None = None
    carbs_g: float | None = None
    fat_g: float | None = None
    fiber_g: float | None = None
    sugar_g: float | None = None
    saturated_fat_g: float | None = None
    trans_fat_g: float | None = None
    monounsaturated_fat_g: float | None = None
    polyunsaturated_fat_g: float | None = None
    cholesterol_mg: float | None = None
    sodium_mg: float | None = None
    potassium_mg: float | None = None
    calcium_mg: float | None = None
    iron_mg: float | None = None
    magnesium_mg: float | None = None
    phosphorus_mg: float | None = None
    zinc_mg: float | None = None
    copper_mg: float | None = None
    manganese_mg: float | None = None
    selenium_ug: float | None = None
    vitamin_a_ug: float | None = None
    vitamin_c_mg: float | None = None
    vitamin_d_ug: float | None = None
    vitamin_e_mg: float | None = None
    vitamin_k_ug: float | None = None
    thiamin_mg: float | None = None
    riboflavin_mg: float | None = None
    niacin_mg: float | None = None
    vitamin_b6_mg: float | None = None
    folate_ug: float | None = None
    vitamin_b12_ug: float | None = None
    water_g: float | None = None
    alcohol_g: float | None = None

    def set_if_missing(self, column: str, value: float | None) -> None:
        if value is None:
            return
        if getattr(self, column) is not None:
            return
        setattr(self, column, value)

    def merge(self, other: NutrientValues) -> NutrientValues:
        out = NutrientValues(**self.as_dict())
        for name in NUTRIENT_COLUMN_NAMES:
            v = getattr(other, name)
            if v is not None:
                setattr(out, name, v)
        return out

    def as_dict(self) -> dict[str, float | None]:
        return {f.name: getattr(self, f.name) for f in fields(self)}

    def non_null_count(self) -> int:
        return sum(1 for f in fields(self) if getattr(self, f.name) is not None)

    def macro_count(self) -> int:
        keys = ("energy_kcal", "protein_g", "carbs_g", "fat_g")
        return sum(1 for k in keys if getattr(self, k) is not None)


def nutrients_from_usda_entries(entries: list[dict[str, Any]]) -> NutrientValues:
    values = NutrientValues()
    for entry in entries:
        nid = entry.get("nutrient", {}).get("id") or entry.get("nutrientId")
        if nid is None:
            continue
        col = USDA_NUTRIENT_ID_MAP.get(int(nid))
        if not col:
            continue
        amount = entry.get("amount")
        if amount is None:
            continue
        values.set_if_missing(col, float(amount))
    return values


def nutrients_from_off_nutriments(nutriments: dict[str, Any]) -> NutrientValues:
    values = NutrientValues()
    for key, raw in nutriments.items():
        if raw is None or key.endswith("_unit") or key.endswith("_value"):
            continue
        col = OFF_NUTRIMENT_MAP.get(key)
        if not col:
            continue
        try:
            values.set_if_missing(col, float(raw))
        except (TypeError, ValueError):
            continue
    # OFF sodium is often in g per 100g
    if values.sodium_mg is not None and values.sodium_mg < 50:
        # heuristic: values < 50 on sodium are likely grams (e.g. 0.4 g → 400 mg)
        if "sodium_100g" in nutriments or "sodium" in nutriments:
            values.sodium_mg = values.sodium_mg * 1000.0
    return values


def nutrients_from_ifct_row(row: dict[str, str]) -> NutrientValues:
    """Map IFCT-style column headers (per 100g) to NutrientValues."""

    def _f(key: str) -> float | None:
        raw = row.get(key, "").strip()
        if not raw or raw in ("-", "NA", "Tr"):
            return None
        try:
            return float(raw)
        except ValueError:
            return None

    return NutrientValues(
        energy_kcal=_f("energy_kcal"),
        protein_g=_f("protein_g"),
        carbs_g=_f("carbs_g"),
        fat_g=_f("fat_g"),
        fiber_g=_f("fiber_g"),
        calcium_mg=_f("calcium_mg"),
        iron_mg=_f("iron_mg"),
        vitamin_c_mg=_f("vitamin_c_mg"),
    )


def iter_nutrient_sql_columns() -> Iterator[str]:
    yield from NUTRIENT_COLUMN_NAMES
