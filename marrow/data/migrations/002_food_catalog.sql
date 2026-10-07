-- M2: unified offline food catalog (per 100g / per 100ml)

CREATE TABLE IF NOT EXISTS foods (
    id INTEGER PRIMARY KEY,
    source TEXT NOT NULL CHECK (source IN ('usda', 'off', 'ifct', 'sample')),
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

CREATE INDEX IF NOT EXISTS idx_foods_name_normalized ON foods (name_normalized);
CREATE INDEX IF NOT EXISTS idx_foods_barcode ON foods (barcode) WHERE barcode IS NOT NULL;

CREATE TABLE IF NOT EXISTS food_nutrients (
    food_id INTEGER PRIMARY KEY REFERENCES foods (id) ON DELETE CASCADE,
    energy_kcal REAL,
    protein_g REAL,
    carbs_g REAL,
    fat_g REAL,
    fiber_g REAL,
    sugar_g REAL,
    saturated_fat_g REAL,
    trans_fat_g REAL,
    monounsaturated_fat_g REAL,
    polyunsaturated_fat_g REAL,
    cholesterol_mg REAL,
    sodium_mg REAL,
    potassium_mg REAL,
    calcium_mg REAL,
    iron_mg REAL,
    magnesium_mg REAL,
    phosphorus_mg REAL,
    zinc_mg REAL,
    copper_mg REAL,
    manganese_mg REAL,
    selenium_ug REAL,
    vitamin_a_ug REAL,
    vitamin_c_mg REAL,
    vitamin_d_ug REAL,
    vitamin_e_mg REAL,
    vitamin_k_ug REAL,
    thiamin_mg REAL,
    riboflavin_mg REAL,
    niacin_mg REAL,
    vitamin_b6_mg REAL,
    folate_ug REAL,
    vitamin_b12_ug REAL,
    water_g REAL,
    alcohol_g REAL
);

CREATE TABLE IF NOT EXISTS food_servings (
    id INTEGER PRIMARY KEY,
    food_id INTEGER NOT NULL REFERENCES foods (id) ON DELETE CASCADE,
    label TEXT NOT NULL,
    amount REAL NOT NULL,
    unit TEXT NOT NULL,
    grams_equivalent REAL NOT NULL,
    is_default INTEGER NOT NULL DEFAULT 0 CHECK (is_default IN (0, 1)),
    sort_order INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_food_servings_food_id ON food_servings (food_id);
