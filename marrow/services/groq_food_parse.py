"""Groq-backed food log parsing (structured JSON only — nutrients come from the DB)."""

from __future__ import annotations

import json
import logging
import re
import sqlite3
from typing import Any, Literal

from marrow.services.diary_parse import _build_draft_item, _name_match_confidence
from marrow.services.food_search import search_foods
from marrow.services.groq_client import GroqClient, GroqClientError, default_client
from marrow.services.recipes import aggregate_recipe_nutrients
from marrow.services.nutrient_validation import collect_nutrient_warnings, nutrients_for_display

log = logging.getLogger(__name__)

MEAL_TAGS = frozenset({"breakfast", "lunch", "dinner", "snack", "pre_workout", "post_workout"})

PARSE_SYSTEM = """You convert messy meal logs into strict JSON. Rules:
- Output ONLY valid JSON matching the schema below.
- Never include calories, macros, or any nutrient numbers.
- Use sensible household units (g, ml, cup, roti, katori, piece, serving, bowl, plate).
- Split combined meals into separate items.
- For composite dishes (curries, biryani, thali, etc.) set dish=true and list ingredients with gram estimates.
Schema:
{"items":[{"food_name":str,"quantity":number,"unit":str,"meal":str,"dish":bool,"ingredients":[{"food_name":str,"grams":number}]}]}
Meal must be one of: breakfast, lunch, dinner, snack, pre_workout, post_workout."""


def _normalize_meal(value: str | None, fallback: str) -> str:
    tag = (value or fallback or "snack").strip().lower()
    return tag if tag in MEAL_TAGS else fallback


def _parse_json_content(raw: str) -> dict[str, Any]:
    text = raw.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence:
        text = fence.group(1).strip()
    return json.loads(text)


def validate_groq_items(payload: dict[str, Any], default_meal: str) -> list[dict[str, Any]]:
    items = payload.get("items")
    if not isinstance(items, list) or not items:
        raise ValueError("items must be a non-empty list")
    cleaned: list[dict[str, Any]] = []
    for entry in items:
        if not isinstance(entry, dict):
            continue
        name = str(entry.get("food_name") or "").strip()
        if not name:
            continue
        try:
            quantity = float(entry.get("quantity", 1))
        except (TypeError, ValueError):
            quantity = 1.0
        if quantity <= 0:
            quantity = 1.0
        unit = str(entry.get("unit") or "serving").strip() or "serving"
        meal = _normalize_meal(entry.get("meal"), default_meal)
        dish = bool(entry.get("dish"))
        ingredients_raw = entry.get("ingredients") if dish else None
        ingredients: list[dict[str, float | str]] = []
        if isinstance(ingredients_raw, list):
            for ing in ingredients_raw:
                if not isinstance(ing, dict):
                    continue
                ing_name = str(ing.get("food_name") or "").strip()
                if not ing_name:
                    continue
                try:
                    grams = float(ing.get("grams"))
                except (TypeError, ValueError):
                    continue
                if grams <= 0:
                    continue
                ingredients.append({"food_name": ing_name, "grams": grams})
        cleaned.append(
            {
                "food_name": name,
                "quantity": quantity,
                "unit": unit,
                "meal": meal,
                "dish": dish and bool(ingredients),
                "ingredients": ingredients,
            }
        )
    if not cleaned:
        raise ValueError("no valid items in Groq payload")
    return cleaned


def _match_ingredient(conn: sqlite3.Connection, food_name: str) -> dict | None:
    search = search_foods(conn, food_name, limit=3)
    results = search.get("results") or []
    return results[0] if results else None


def _build_decomposition_draft(
    conn: sqlite3.Connection,
    segment_raw: str,
    dish_name: str,
    quantity: float,
    unit: str,
    ingredients: list[dict[str, Any]],
) -> dict:
    from marrow.services.food_text_parser import new_draft_id

    breakdown: list[dict[str, Any]] = []
    scaled_for_sum: list[dict[str, Any]] = []
    for ing in ingredients:
        hit = _match_ingredient(conn, str(ing["food_name"]))
        if not hit:
            breakdown.append(
                {
                    "food_name": ing["food_name"],
                    "food_id": None,
                    "grams": float(ing["grams"]),
                    "energy_kcal": None,
                }
            )
            continue
        food_id = int(hit["id"])
        grams = float(ing["grams"])
        breakdown.append(
            {
                "food_name": hit["name"],
                "food_id": food_id,
                "grams": grams,
                "energy_kcal": None,
            }
        )
        scaled_for_sum.append({"food_id": food_id, "grams": grams})

    nutrients: dict[str, float | None] = {}
    energy = None
    grams_total = sum(float(i["grams"]) for i in breakdown)
    warnings: list[str] = ["dish_decomposition"]
    if scaled_for_sum:
        try:
            nutrients = nutrients_for_display(aggregate_recipe_nutrients(conn, scaled_for_sum))
            energy = nutrients.get("energy_kcal")
            for row in breakdown:
                if row["food_id"] is None:
                    continue
                from marrow.data.foods.units import scale_nutrients
                from marrow.services.food_repository import fetch_nutrients

                basis = conn.execute(
                    "SELECT basis FROM foods WHERE id = ?", (row["food_id"],)
                ).fetchone()
                if basis:
                    per = fetch_nutrients(conn, int(row["food_id"]))
                    scaled = scale_nutrients(per, float(row["grams"]), basis["basis"])
                    row["energy_kcal"] = scaled.get("energy_kcal")
        except ValueError as exc:
            warnings.append(str(exc))

    if any(row["food_id"] is None for row in breakdown):
        warnings.append("decomposition_partial_match")

    primary_id = next((row["food_id"] for row in breakdown if row["food_id"] is not None), None)
    confidence: Literal["EXACT", "GOOD", "ESTIMATED"] = "ESTIMATED"
    if primary_id:
        confidence = _name_match_confidence(dish_name, dish_name, 0.0)

    macro_warnings = collect_nutrient_warnings(
        energy_kcal=energy,
        protein_g=nutrients.get("protein_g"),
        carbs_g=nutrients.get("carbs_g"),
        fat_g=nutrients.get("fat_g"),
        grams_equivalent=grams_total,
        serving_note="Groq dish decomposition (DB totals only)",
    )
    warnings.extend(macro_warnings)

    return {
        "draft_id": new_draft_id(),
        "raw_fragment": segment_raw,
        "amount": quantity,
        "unit": unit,
        "food_query": dish_name,
        "food_id": primary_id,
        "food_name": dish_name,
        "match_confidence": confidence,
        "energy_kcal": energy,
        "nutrients": nutrients,
        "grams_equivalent": grams_total,
        "warnings": warnings,
        "conversion_note": "Decomposed dish; nutrients summed from matched ingredients",
        "decomposition": breakdown,
        "recipe_cache_name": dish_name,
        "alternatives": [],
    }


def groq_items_to_drafts(
    conn: sqlite3.Connection,
    groq_items: list[dict[str, Any]],
    *,
    source_text: str,
) -> list[dict]:
    drafts: list[dict] = []
    for item in groq_items:
        segment = f"{item['quantity']} {item['unit']} {item['food_name']}".strip()
        if item.get("dish") and item.get("ingredients"):
            dish_draft = _build_decomposition_draft(
                conn,
                segment,
                str(item["food_name"]),
                float(item["quantity"]),
                str(item["unit"]),
                list(item["ingredients"]),
            )
            dish_draft["_meal_tag"] = item["meal"]
            drafts.append(dish_draft)
            continue
        search = search_foods(conn, str(item["food_name"]), limit=5)
        results = search.get("results") or []
        hit = results[0] if results else None
        draft = _build_draft_item(
            conn,
            segment,
            float(item["quantity"]),
            str(item["unit"]),
            str(item["food_name"]),
            hit,
        )
        draft["_meal_tag"] = item["meal"]
        if len(results) > 1:
            draft["alternatives"] = [
                {"id": r["id"], "name": r["name"], "rank": r.get("rank")} for r in results[1:5]
            ]
        drafts.append(draft)
    return drafts


def parse_food_text_with_groq(
    conn: sqlite3.Connection,
    text: str,
    *,
    meal_tag: str = "snack",
    client: GroqClient | None = None,
) -> list[dict] | None:
    groq = client or default_client()
    if not groq.available:
        return None
    user = f"Meal context: {meal_tag}\nLog text:\n{text.strip()}"
    try:
        content = groq.chat_completion(
            [
                {"role": "system", "content": PARSE_SYSTEM},
                {"role": "user", "content": user},
            ],
            temperature=0.0,
            response_format={"type": "json_object"},
        )
        payload = _parse_json_content(content)
        items = validate_groq_items(payload, meal_tag)
        return groq_items_to_drafts(conn, items, source_text=text)
    except (GroqClientError, ValueError, json.JSONDecodeError) as exc:
        log.info("Groq parse skipped: %s", exc)
        return None
