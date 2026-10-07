-- M5: optional pre/post-workout meal tags on diary_logs

PRAGMA foreign_keys = OFF;

CREATE TABLE diary_logs_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    log_date TEXT NOT NULL,
    meal_tag TEXT NOT NULL DEFAULT 'snack'
        CHECK (meal_tag IN (
            'breakfast', 'lunch', 'dinner', 'snack',
            'pre_workout', 'post_workout'
        )),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    source_text TEXT,
    notes TEXT
);

INSERT INTO diary_logs_new (id, log_date, meal_tag, created_at, source_text, notes)
SELECT id, log_date, meal_tag, created_at, source_text, notes FROM diary_logs;

DROP TABLE diary_logs;
ALTER TABLE diary_logs_new RENAME TO diary_logs;

CREATE INDEX IF NOT EXISTS idx_diary_logs_date ON diary_logs(log_date);

PRAGMA foreign_keys = ON;
