"""Daily diary nutrient aggregation and placeholder targets (M5)."""

from __future__ import annotations

from typing import Any

# Placeholder until M6 onboarding / goals — surfaced in UI as "budget".
PLACEHOLDER_DAILY_TARGETS: dict[str, float] = {
    "energy_kcal": 2200.0,
    "protein_g": 150.0,
    "carbs_g": 220.0,
    "fat_g": 70.0,
}

MACRO_KEYS = ("energy_kcal", "protein_g", "carbs_g", "fat_g")

MEAL_DISPLAY_ORDER = (
    "breakfast",
    "lunch",
    "snack",
    "dinner",
    "pre_workout",
    "post_workout",
)


def _sum_field(entries: list[dict[str, Any]], field: str) -> float | None:
    if not entries:
        return None
    total = 0.0
    for entry in entries:
        value = entry.get(field)
        if value is None:
            return None
        total += float(value)
    return round(total, 1)


def summarize_diary_nutrients(entries: list[dict[str, Any]]) -> dict[str, float | None]:
    """Sum scaled entry macros; any NULL input makes that nutrient total NULL."""
    return {key: _sum_field(entries, key) for key in MACRO_KEYS}


def remaining_budget(
    consumed: dict[str, float | None],
    targets: dict[str, float] | None = None,
) -> dict[str, float | None]:
    budget = targets or PLACEHOLDER_DAILY_TARGETS
    remaining: dict[str, float | None] = {}
    for key in MACRO_KEYS:
        used = consumed.get(key)
        target = budget.get(key)
        if used is None or target is None:
            remaining[key] = None
        else:
            remaining[key] = round(float(target) - float(used), 1)
    return remaining


def group_entries_by_meal(
    entries: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Stable meal sections in display order."""
    buckets: dict[str, list[dict[str, Any]]] = {tag: [] for tag in MEAL_DISPLAY_ORDER}
    other: list[dict[str, Any]] = []
    for entry in entries:
        tag = str(entry.get("meal_tag") or "snack").lower()
        if tag in buckets:
            buckets[tag].append(entry)
        else:
            other.append(entry)

    sections: list[dict[str, Any]] = []
    for tag in MEAL_DISPLAY_ORDER:
        items = buckets[tag]
        if not items:
            continue
        sections.append(
            {
                "meal_tag": tag,
                "entries": items,
                "totals": summarize_diary_nutrients(items),
            }
        )
    if other:
        sections.append(
            {
                "meal_tag": "other",
                "entries": other,
                "totals": summarize_diary_nutrients(other),
            }
        )
    return sections
