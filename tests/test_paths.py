"""Path helpers."""

from marrow.core.paths import (
    APP_NAME,
    app_data_dir,
    bundled_foods_catalog_path,
    database_path,
    install_root,
    migrations_dir,
)


def test_app_data_dir_contains_app_name():
    assert APP_NAME in str(app_data_dir())
    assert app_data_dir().exists()


def test_database_under_app_data():
    assert database_path().parent == app_data_dir()


def test_bundled_foods_catalog_in_repo():
    path = bundled_foods_catalog_path()
    assert path.name == "foods_catalog.sqlite"
    assert path.exists()


def test_install_root_has_migrations():
    assert migrations_dir().is_dir()
    assert any(migrations_dir().glob("*.sql"))
    assert (install_root() / "marrow").is_dir()
