-- M6: onboarding, macro/micro targets, weight log

ALTER TABLE user_profile ADD COLUMN age_years INTEGER;
ALTER TABLE user_profile ADD COLUMN sex TEXT CHECK (sex IS NULL OR sex IN ('male', 'female'));
ALTER TABLE user_profile ADD COLUMN height_cm REAL;
ALTER TABLE user_profile ADD COLUMN weight_kg REAL;
ALTER TABLE user_profile ADD COLUMN activity_level TEXT CHECK (
    activity_level IS NULL OR activity_level IN (
        'sedentary', 'light', 'moderate', 'active', 'very_active'
    )
);
ALTER TABLE user_profile ADD COLUMN goal TEXT CHECK (
    goal IS NULL OR goal IN ('cut', 'maintain', 'lean_bulk')
);
ALTER TABLE user_profile ADD COLUMN calorie_tolerance_pct REAL NOT NULL DEFAULT 5.0;
ALTER TABLE user_profile ADD COLUMN use_split_day_targets INTEGER NOT NULL DEFAULT 0;
ALTER TABLE user_profile ADD COLUMN gym_weekdays TEXT;
ALTER TABLE user_profile ADD COLUMN disclaimer_acknowledged_at TEXT;
ALTER TABLE user_profile ADD COLUMN onboarding_completed_at TEXT;

CREATE TABLE IF NOT EXISTS daily_macro_targets (
    day_kind TEXT PRIMARY KEY CHECK (day_kind IN ('default', 'gym', 'rest')),
    energy_kcal REAL NOT NULL,
    protein_g REAL NOT NULL,
    carbs_g REAL NOT NULL,
    fat_g REAL NOT NULL,
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS micronutrient_targets (
    nutrient_key TEXT PRIMARY KEY,
    target_value REAL NOT NULL,
    unit TEXT NOT NULL,
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS weight_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    logged_date TEXT NOT NULL,
    weight_kg REAL NOT NULL CHECK (weight_kg > 0),
    note TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_weight_log_date ON weight_log (logged_date DESC);
