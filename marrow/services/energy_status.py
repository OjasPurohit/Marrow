"""Daily calorie balance classification (M6)."""

from __future__ import annotations

from typing import Literal

EnergyStatus = Literal["DEFICIT", "ON_TARGET", "SURPLUS"]


def classify_energy_balance(
    consumed_kcal: float | None,
    target_kcal: float,
    tolerance_pct: float = 5.0,
) -> dict:
    """
    Compare intake to target with a symmetric percent band.

    energy_delta_kcal = consumed - target (positive means surplus vs target).
    """
    if consumed_kcal is None or target_kcal <= 0:
        return {
            "status": None,
            "energy_delta_kcal": None,
            "tolerance_pct": tolerance_pct,
            "tolerance_kcal": round(target_kcal * tolerance_pct / 100.0, 1)
            if target_kcal > 0
            else None,
        }

    delta = round(float(consumed_kcal) - float(target_kcal), 1)
    band = float(target_kcal) * float(tolerance_pct) / 100.0
    if delta < -band:
        status: EnergyStatus = "DEFICIT"
    elif delta > band:
        status = "SURPLUS"
    else:
        status = "ON_TARGET"

    return {
        "status": status,
        "energy_delta_kcal": delta,
        "tolerance_pct": tolerance_pct,
        "tolerance_kcal": round(band, 1),
    }
