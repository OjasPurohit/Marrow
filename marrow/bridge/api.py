"""pywebview `js_api` surface exposed to the frontend."""

from __future__ import annotations

from marrow.core.config import load_window_geometry, save_window_geometry
from marrow.core.groq_settings import (
    clear_groq_api_key,
    groq_settings_public,
    save_groq_settings,
    set_groq_api_key,
)
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
from marrow.services.user_profile import (
    complete_onboarding,
    get_user_profile,
    preview_metabolic_plan,
    update_macro_targets,
)
from marrow.services.night_review import get_night_review
from marrow.services.voice_input import capture_and_transcribe, get_last_voice_transcript
from marrow.services.diary_history import get_diary_history_month, get_diary_history_range
from marrow.services.trends import get_trend_series
from marrow.services.weight_log import (
    add_weight_entry,
    delete_weight_entry,
    get_weight_log_with_trend,
    list_weight_entries,
)


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

    def get_night_review(self, log_date: str | None = None) -> dict:
        with session() as conn:
            return get_night_review(conn, log_date)

    def get_user_profile(self) -> dict:
        with session() as conn:
            return get_user_profile(conn)

    def preview_metabolic_plan(self, payload: dict) -> dict:
        return preview_metabolic_plan(payload)

    def complete_onboarding(self, payload: dict) -> dict:
        with session() as conn:
            return complete_onboarding(conn, payload)

    def update_macro_targets(self, payload: dict) -> dict:
        with session() as conn:
            return update_macro_targets(conn, payload)

    def add_weight_entry(self, payload: dict) -> dict:
        with session() as conn:
            return add_weight_entry(
                conn,
                float(payload["weight_kg"]),
                logged_date=payload.get("logged_date"),
                note=payload.get("note"),
            )

    def list_weight_entries(self, limit: int = 90) -> list:
        with session() as conn:
            return list_weight_entries(conn, limit=limit)

    def get_weight_log_with_trend(self, limit: int = 90) -> dict:
        with session() as conn:
            return get_weight_log_with_trend(conn, limit=limit)

    def delete_weight_entry(self, entry_id: int) -> dict:
        with session() as conn:
            return delete_weight_entry(conn, int(entry_id))

    def get_diary_history_range(self, start_date: str | None = None, end_date: str | None = None) -> dict:
        with session() as conn:
            return get_diary_history_range(conn, start_date, end_date)

    def get_diary_history_month(self, year: int, month: int) -> dict:
        with session() as conn:
            return get_diary_history_month(conn, int(year), int(month))

    def get_trend_series(
        self,
        range_days: int = 30,
        micronutrient_keys: list | None = None,
        end_date: str | None = None,
    ) -> dict:
        with session() as conn:
            return get_trend_series(
                conn,
                int(range_days),
                micronutrient_keys=micronutrient_keys,
                end_date=end_date,
            )

    def get_groq_settings(self) -> dict:
        return groq_settings_public()

    def update_groq_settings(self, payload: dict) -> dict:
        allowed = {
            "chat_model",
            "whisper_model",
            "request_timeout_sec",
            "max_retries",
            "enable_night_summary",
            "enable_voice_hotkey",
            "voice_hotkey",
            "voice_record_seconds",
        }
        updates = {k: payload[k] for k in allowed if k in payload}
        return save_groq_settings(updates)

    def set_groq_api_key(self, api_key: str) -> dict:
        set_groq_api_key(str(api_key))
        return groq_settings_public()

    def clear_groq_api_key(self) -> dict:
        clear_groq_api_key()
        return groq_settings_public()

    def transcribe_voice_note(self, duration_sec: float | None = None) -> dict:
        try:
            text = capture_and_transcribe(duration_sec)
            return {"text": text, "error": None}
        except Exception as exc:  # noqa: BLE001 — bridge surface
            return {"text": None, "error": str(exc)}

    def poll_voice_transcript(self, clear: bool = True) -> dict:
        return get_last_voice_transcript(clear=bool(clear))
