"""Path helpers."""

from marrow.core.paths import APP_NAME, app_data_dir, database_path


def test_app_data_dir_contains_app_name():
    assert APP_NAME in str(app_data_dir())
    assert app_data_dir().exists()


def test_database_under_app_data():
    assert database_path().parent == app_data_dir()
