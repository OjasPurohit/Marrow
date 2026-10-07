"""pywebview `js_api` surface exposed to the frontend."""

from __future__ import annotations

from marrow.core.config import load_window_geometry, save_window_geometry
from marrow.data.catalog_seed import catalog_seed_status
from marrow.data.database import session
from marrow.services.app_info import get_app_info
from marrow.services.custom_foods import create_custom_food
from marrow.services.food_detail import convert_food_serving, get_food_detail
from marrow.services.food_repository import fetch_servings
from marrow.services.food_search import search_foods
from marrow.services.diary_log import (
    confirm_and_save_log,
    get_daily_nutrient_totals,
    list_diary_entries_for_date,
)
from marrow.services.diary_parse import parse_food_text
from marrow.services.recipes import create_recipe, get_recipe


class BridgeApi:
    """Methods are callable from JS via `window.pywebview.api.<name>()`."""

    def ping(self) -> str:
        return "ok"

    def get_app_info(self) -> dict:
        return get_app_info()

    def get_window_geometry(self) -> dict:
        return load_window_geometry()

    def save_window_geometry(self, x: int, y: int, width: int, height: int) -> bool:
        save_window_geometry(int(x), int(y), int(width), int(height))
        return True

    def get_catalog_seed_status(self) -> dict:
        with session() as conn:
            return catalog_seed_status(conn)

    def search_foods(self, query: str, limit: int = 25) -> dict:
        with session() as conn:
            return search_foods(conn, query, limit=limit)

    def get_food_detail(self, food_id: int) -> dict | None:
        with session() as conn:
            return get_food_detail(conn, int(food_id))

    def get_food_servings(self, food_id: int) -> list:
        with session() as conn:
            return fetch_servings(conn, int(food_id))

    def convert_food_serving(
        self,
        food_id: int,
        amount: float,
        unit: str,
        target_preparation: str | None = None,
    ) -> dict:
        with session() as conn:
            return convert_food_serving(
                conn,
                int(food_id),
                float(amount),
                unit,
                target_preparation=target_preparation,
            )

    def create_custom_food(self, payload: dict) -> dict:
        with session() as conn:
            return create_custom_food(
                conn,
                str(payload.get("name", "")),
                payload.get("nutrients") or {},
                basis=str(payload.get("basis") or "per_100g"),
                preparation=str(payload.get("preparation") or "unknown"),
                brand=payload.get("brand"),
            )

    def create_recipe(self, payload: dict) -> dict:
        with session() as conn:
            return create_recipe(
                conn,
                str(payload.get("name", "")),
                float(payload.get("servings_count") or 1),
                list(payload.get("ingredients") or []),
                notes=payload.get("notes"),
            )

    def get_recipe(self, recipe_id: int) -> dict | None:
        with session() as conn:
            return get_recipe(conn, int(recipe_id))

    def parse_food_text(self, text: str, meal_tag: str = "snack") -> dict:
        with session() as conn:
            return parse_food_text(conn, text, meal_tag=meal_tag)

    def confirm_and_save_log(self, payload: dict) -> dict:
        with session() as conn:
            return confirm_and_save_log(conn, payload)

    def list_diary_entries_for_date(self, log_date: str | None = None) -> dict:
        with session() as conn:
            return list_diary_entries_for_date(conn, log_date)

    def get_daily_nutrient_totals(self, log_date: str | None = None) -> dict:
        with session() as conn:
            return get_daily_nutrient_totals(conn, log_date)
