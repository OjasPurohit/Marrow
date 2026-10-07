-- M3: FTS5 search, custom foods source, recipes, favorites, recents

PRAGMA foreign_keys = OFF;

CREATE TABLE foods_m3 (
    id INTEGER PRIMARY KEY,
    source TEXT NOT NULL CHECK (source IN ('usda', 'off', 'ifct', 'sample', 'custom')),
    source_food_id TEXT NOT NULL,
    name TEXT NOT NULL,
    name_normalized TEXT NOT NULL,
    basis TEXT NOT NULL CHECK (basis IN ('per_100g', 'per_100ml')),
    preparation TEXT NOT NULL DEFAULT 'unknown'
        CHECK (preparation IN ('raw', 'cooked', 'unknown')),
    data_quality TEXT NOT NULL DEFAULT 'medium'
        CHECK (data_quality IN ('high', 'medium', 'low', 'estimated')),
    brand TEXT,
    barcode TEXT,
    locale TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (source, source_food_id)
);

INSERT INTO foods_m3 SELECT * FROM foods;
DROP TABLE foods;
ALTER TABLE foods_m3 RENAME TO foods;

CREATE INDEX IF NOT EXISTS idx_foods_name_normalized ON foods (name_normalized);
CREATE INDEX IF NOT EXISTS idx_foods_barcode ON foods (barcode) WHERE barcode IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_foods_source ON foods (source);

PRAGMA foreign_keys = ON;

-- FTS5: search-as-you-type on name, normalized name, brand
CREATE VIRTUAL TABLE IF NOT EXISTS foods_fts USING fts5(
    name,
    name_normalized,
    brand,
    content='foods',
    content_rowid='id',
    tokenize='unicode61 remove_diacritics 2'
);

CREATE TRIGGER IF NOT EXISTS foods_ai AFTER INSERT ON foods BEGIN
    INSERT INTO foods_fts(rowid, name, name_normalized, brand)
    VALUES (new.id, new.name, new.name_normalized, new.brand);
END;

CREATE TRIGGER IF NOT EXISTS foods_ad AFTER DELETE ON foods BEGIN
    INSERT INTO foods_fts(foods_fts, rowid, name, name_normalized, brand)
    VALUES ('delete', old.id, old.name, old.name_normalized, old.brand);
END;

CREATE TRIGGER IF NOT EXISTS foods_au AFTER UPDATE ON foods BEGIN
    INSERT INTO foods_fts(foods_fts, rowid, name, name_normalized, brand)
    VALUES ('delete', old.id, old.name, old.name_normalized, old.brand);
    INSERT INTO foods_fts(rowid, name, name_normalized, brand)
    VALUES (new.id, new.name, new.name_normalized, new.brand);
END;

-- User recipes (ingredients reference catalog/custom foods)
CREATE TABLE IF NOT EXISTS recipes (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    name_normalized TEXT NOT NULL,
    servings_count REAL NOT NULL DEFAULT 1 CHECK (servings_count > 0),
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_recipes_name_normalized ON recipes (name_normalized);

CREATE TABLE IF NOT EXISTS recipe_ingredients (
    id INTEGER PRIMARY KEY,
    recipe_id INTEGER NOT NULL REFERENCES recipes (id) ON DELETE CASCADE,
    food_id INTEGER NOT NULL REFERENCES foods (id),
    grams REAL NOT NULL CHECK (grams > 0),
    sort_order INTEGER NOT NULL DEFAULT 0,
    note TEXT
);

CREATE INDEX IF NOT EXISTS idx_recipe_ingredients_recipe_id ON recipe_ingredients (recipe_id);

CREATE TABLE IF NOT EXISTS food_favorites (
    food_id INTEGER PRIMARY KEY REFERENCES foods (id) ON DELETE CASCADE,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS food_recents (
    food_id INTEGER PRIMARY KEY REFERENCES foods (id) ON DELETE CASCADE,
    last_used_at TEXT NOT NULL DEFAULT (datetime('now')),
    use_count INTEGER NOT NULL DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_food_recents_last_used ON food_recents (last_used_at DESC);

-- Backfill FTS from any existing food rows (e.g. after table rebuild).
INSERT INTO foods_fts(foods_fts) VALUES ('rebuild');
