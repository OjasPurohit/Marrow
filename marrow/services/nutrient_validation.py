"""Nutrient consistency and portion sanity checks for diary confirmation."""

from __future__ import annotations

from typing import Literal

WarningCode = Literal[
    "macro_kcal_mismatch",
    "portion_very_large",
    "energy_very_high",
    "estimated_serving",
]


def implied_energy_kcal(
    protein_g: float | None,
    carbs_g: float | None,
    fat_g: float | None,
) -> float | None:
    if protein_g is None or carbs_g is None or fat_g is None:
        return None
    return 4.0 * protein_g + 4.0 * carbs_g + 9.0 * fat_g


def macro_kcal_consistent(
    energy_kcal: float | None,
    protein_g: float | None,
    carbs_g: float | None,
    fat_g: float | None,
    tolerance: float = 0.10,
) -> bool | None:
    """True if within tolerance; None if not enough data to check."""
    if energy_kcal is None or energy_kcal <= 0:
        return None
    implied = implied_energy_kcal(protein_g, carbs_g, fat_g)
    if implied is None or implied <= 0:
        return None
    delta = abs(energy_kcal - implied) / energy_kcal
    return delta <= tolerance


def collect_nutrient_warnings(
    *,
    energy_kcal: float | None,
    protein_g: float | None,
    carbs_g: float | None,
    fat_g: float | None,
    grams_equivalent: float,
    serving_note: str | None = None,
) -> list[str]:
    warnings: list[str] = []
    consistent = macro_kcal_consistent(energy_kcal, protein_g, carbs_g, fat_g)
    if consistent is False:
        warnings.append("macro_kcal_mismatch")
    if grams_equivalent > 1500:
        warnings.append("portion_very_large")
    if energy_kcal is not None and energy_kcal > 2000:
        warnings.append("energy_very_high")
    if serving_note in ("default_piece_weight", "volume_assumed_water_density"):
        warnings.append("estimated_serving")
    return warnings


def nutrients_for_display(nutrients: dict[str, float | None]) -> dict[str, float | None]:
    """Pass through; callers must not coerce NULL to zero."""
    return {k: (None if v is None else float(v)) for k, v in nutrients.items()}
