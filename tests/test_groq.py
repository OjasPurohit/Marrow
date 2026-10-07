"""Groq integration tests (mocked HTTP — no live API calls)."""

import json
import pytest

from marrow.core.groq_settings import (
    clear_groq_api_key,
    groq_configured,
    groq_settings_public,
    set_groq_api_key,
)
from marrow.services.diary_parse import parse_food_text
from marrow.services.groq_client import GroqClient, GroqClientError
from marrow.services.groq_food_parse import (
    parse_food_text_with_groq,
    validate_groq_items,
)
from marrow.services.groq_night_summary import maybe_groq_night_summary
from marrow.services.night_review import get_night_review


def test_groq_settings_keyring_roundtrip(monkeypatch):
    store: dict[str, str] = {}

    def fake_get(service, account):
        return store.get(f"{service}:{account}")

    def fake_set(service, account, password):
        store[f"{service}:{account}"] = password

    def fake_delete(service, account):
        store.pop(f"{service}:{account}", None)

    monkeypatch.setattr("keyring.get_password", fake_get)
    monkeypatch.setattr("keyring.set_password", fake_set)
    monkeypatch.setattr("keyring.delete_password", fake_delete)

    assert groq_configured() is False
    set_groq_api_key("sk-test")
    assert groq_configured() is True
    pub = groq_settings_public()
    assert pub["configured"] is True
    assert "chat_model" in pub
    clear_groq_api_key()
    assert groq_configured() is False


def test_validate_groq_items_schema():
    payload = {
        "items": [
            {
                "food_name": "banana",
                "quantity": 1,
                "unit": "medium",
                "meal": "snack",
                "dish": False,
            }
        ]
    }
    items = validate_groq_items(payload, "lunch")
    assert items[0]["food_name"] == "banana"
    assert items[0]["meal"] == "snack"


def test_groq_client_retries_on_429():
    calls = {"n": 0}

    def transport(req, timeout=30.0):
        calls["n"] += 1
        if calls["n"] == 1:
            raise GroqClientError("rate limited", status=429, retryable=True)
        return {
            "choices": [{"message": {"content": '{"items":[]}'}}],
        }

    client = GroqClient("sk-test", settings={"request_timeout_sec": 5, "max_retries": 2}, transport=transport)
    text = client.chat_completion([{"role": "user", "content": "hi"}])
    assert "items" in text
    assert calls["n"] == 2


def test_parse_food_text_uses_groq_when_local_misses(user_db, monkeypatch):
    monkeypatch.setattr("marrow.services.diary_parse.groq_configured", lambda: True)

    groq_payload = {
        "items": [
            {
                "food_name": "banana",
                "quantity": 1,
                "unit": "medium",
                "meal": "breakfast",
                "dish": False,
            }
        ]
    }

    def fake_groq(conn, text, meal_tag="snack", client=None):
        from marrow.services.groq_food_parse import groq_items_to_drafts, validate_groq_items

        items = validate_groq_items(groq_payload, meal_tag)
        return groq_items_to_drafts(conn, items, source_text=text)

    monkeypatch.setattr("marrow.services.groq_food_parse.parse_food_text_with_groq", fake_groq)

    result = parse_food_text(user_db, "mystery fruit thing", meal_tag="breakfast")
    assert result["parser"] == "groq"
    assert result["groq_used"] is True
    assert result["items"]
    assert result["items"][0]["food_id"] is not None


def test_maybe_groq_night_summary_mocked(monkeypatch):
    monkeypatch.setattr("marrow.services.groq_night_summary.groq_configured", lambda: True)

    def transport(req, timeout=30.0):
        return {
            "choices": [{"message": {"content": "You hit protein but sodium ran high."}}],
        }

    client = GroqClient("sk-test", transport=transport)
    summary = maybe_groq_night_summary(
        {"status": "ON_TARGET", "energy_delta_kcal": 0},
        {"energy_kcal": 2000, "protein_g": 150, "carbs_g": 200, "fat_g": 70},
        ["Calories landed within your target band today."],
        [],
        client=client,
    )
    assert summary == "You hit protein but sodium ran high."


def test_get_night_review_groq_summary_none_without_key(user_db):
    review = get_night_review(user_db)
    assert review["groq_summary"] is None
