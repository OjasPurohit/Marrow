-- M4: diary meals and log entries

CREATE TABLE IF NOT EXISTS diary_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    log_date TEXT NOT NULL,
    meal_tag TEXT NOT NULL DEFAULT 'snack'
        CHECK (meal_tag IN ('breakfast', 'lunch', 'dinner', 'snack')),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    source_text TEXT,
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_diary_logs_date ON diary_logs(log_date);

CREATE TABLE IF NOT EXISTS diary_log_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    log_id INTEGER NOT NULL REFERENCES diary_logs(id) ON DELETE CASCADE,
    food_id INTEGER NOT NULL REFERENCES foods(id),
    food_name TEXT NOT NULL,
    amount REAL NOT NULL CHECK (amount > 0),
    unit TEXT NOT NULL,
    grams_equivalent REAL NOT NULL,
    energy_kcal REAL,
    protein_g REAL,
    carbs_g REAL,
    fat_g REAL,
    match_confidence TEXT NOT NULL DEFAULT 'ESTIMATED'
        CHECK (match_confidence IN ('EXACT', 'GOOD', 'ESTIMATED')),
    raw_fragment TEXT,
    position INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_diary_entries_log ON diary_log_entries(log_id);
CREATE INDEX IF NOT EXISTS idx_diary_entries_food ON diary_log_entries(food_id);
