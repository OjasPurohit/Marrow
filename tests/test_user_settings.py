from marrow.core.user_settings import load_user_settings, save_user_settings


def test_user_settings_roundtrip(tmp_path, monkeypatch):
    cfg = tmp_path / "config.json"
    monkeypatch.setattr("marrow.core.config.config_path", lambda: cfg)
    defaults = load_user_settings()
    assert defaults["theme"] == "system"
    updated = save_user_settings(
        {
            "theme": "dark",
            "ui_scale": "1.125",
            "reduced_motion": True,
            "units": "imperial",
        }
    )
    assert updated["theme"] == "dark"
    assert updated["ui_scale"] == "1.125"
    assert updated["reduced_motion"] is True
    assert load_user_settings()["units"] == "imperial"
