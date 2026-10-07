"""Backup, export, and import integrity tests."""

import sqlite3

from marrow.services.backup import (
    create_backup_file,
    export_diary_csv_text,
    export_user_json,
    import_diary_csv,
    import_user_json,
    list_backups,
    restore_backup_file,
)
from marrow.services.diary_log import confirm_and_save_log


def _save_sample_log(conn):
    foods = conn.execute("SELECT id, name FROM foods LIMIT 1").fetchone()
    assert foods
    confirm_and_save_log(
        conn,
        {
            "meal_tag": "lunch",
            "source_text": "1 serving test",
            "items": [
                {
                    "food_id": int(foods["id"]),
                    "amount": 1.0,
                    "unit": "serving",
                    "match_confidence": "GOOD",
                    "raw_fragment": "1 serving",
                }
            ],
        },
    )


def test_json_export_import_roundtrip(user_db):
    _save_sample_log(user_db)
    before_entries = user_db.execute("SELECT COUNT(*) FROM diary_log_entries").fetchone()[0]
    payload = export_user_json(user_db)
    user_db.execute("DELETE FROM diary_log_entries")
    user_db.execute("DELETE FROM diary_logs")
    assert user_db.execute("SELECT COUNT(*) FROM diary_log_entries").fetchone()[0] == 0

    stats = import_user_json(user_db, payload)
    after_entries = user_db.execute("SELECT COUNT(*) FROM diary_log_entries").fetchone()[0]
    assert after_entries == before_entries
    assert stats["diary_entries"] == before_entries


def test_json_checksum_detects_tampering(user_db):
    payload = export_user_json(user_db)
    payload["checksum"] = "deadbeef"
    try:
        import_user_json(user_db, payload)
        assert False, "expected checksum failure"
    except ValueError as exc:
        assert "checksum" in str(exc).lower()


def test_csv_export_import(user_db):
    _save_sample_log(user_db)
    csv_text = export_diary_csv_text(user_db)
    user_db.execute("DELETE FROM diary_log_entries")
    user_db.execute("DELETE FROM diary_logs")
    stats = import_diary_csv(user_db, csv_text)
    assert stats["diary_entries"] >= 1


def test_rotating_file_backup_and_restore(user_db, tmp_path):
    _save_sample_log(user_db)
    info = create_backup_file()
    assert info["filename"].startswith("marrow-")
    backups = list_backups()
    assert any(b["filename"] == info["filename"] for b in backups)

    user_db.execute("DELETE FROM diary_log_entries")
    user_db.commit()
    user_db.close()
    restore_backup_file(info["filename"])
    conn2 = sqlite3.connect(str(tmp_path / "marrow.db"))
    conn2.row_factory = sqlite3.Row
    count = conn2.execute("SELECT COUNT(*) FROM diary_log_entries").fetchone()[0]
    conn2.close()
    assert count >= 1
