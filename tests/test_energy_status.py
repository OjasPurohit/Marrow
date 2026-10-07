"""Energy balance classification tests."""

from marrow.services.energy_status import classify_energy_balance


def test_on_target_within_band():
    result = classify_energy_balance(2050.0, 2000.0, tolerance_pct=5.0)
    assert result["status"] == "ON_TARGET"
    assert result["energy_delta_kcal"] == 50.0


def test_deficit_below_band():
    result = classify_energy_balance(1800.0, 2000.0, tolerance_pct=5.0)
    assert result["status"] == "DEFICIT"
    assert result["energy_delta_kcal"] == -200.0


def test_surplus_above_band():
    result = classify_energy_balance(2200.0, 2000.0, tolerance_pct=5.0)
    assert result["status"] == "SURPLUS"


def test_null_consumed():
    result = classify_energy_balance(None, 2000.0)
    assert result["status"] is None
    assert result["energy_delta_kcal"] is None


def test_edge_exactly_at_band():
    # 5% of 2000 = 100; delta -100 is still ON_TARGET (not strictly less than -band)
    result = classify_energy_balance(1900.0, 2000.0, tolerance_pct=5.0)
    assert result["status"] == "ON_TARGET"
