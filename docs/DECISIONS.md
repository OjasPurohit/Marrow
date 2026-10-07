# Marrow — Architecture & product decisions

Recorded decisions for the Marrow build. When the [Apple design reference](https://github.com/emilkowalski/skills/tree/main/skills/apple-design) conflicts with an early spec draft on UI feel, the reference wins.

## 2025-10-07 — M1 scaffold

### Frontend framework: **Svelte 5**

- **Why:** Small runtime, excellent reactivity for a desktop shell, and straightforward integration with the `motion` package for spring-driven, interruptible gestures (per design reference). React would also work; Svelte keeps the UI layer lean for an offline-first desktop app.

### Motion: **`motion` (motion.dev)**

- Springs for gesture handoff, sheets, and lab demos; CSS transitions only for simple hover/press feedback per animate skill hierarchy.

### Database location

- **Windows:** `%LOCALAPPDATA%\Marrow\marrow.db` (and `config.json` for window state).
- **Other platforms (dev):** `~/.local/share/Marrow/` — same layout for local development on Linux/macOS.

### Dev vs production UI

- **Dev:** Vite dev server at `http://127.0.0.1:5173` when `MARROW_DEV=1` or when `ui/dist` is missing.
- **Prod:** Static files from `ui/dist/index.html` relative to the application bundle.

### WebView2

- Production target is Edge WebView2 on Windows. On Linux dev, pywebview uses GTK/WebKit; WebView2 install guidance is shown only when the runtime reports WebView2 as required and missing.

### SQLite migrations

- Versioned SQL files in `marrow/data/migrations/`; applied sequentially on startup; `schema_migrations` table tracks applied versions.

### Large bundled data (>50MB)

- Full USDA Foundation / Branded JSON dumps and full OFF exports stay **out of git**. Rebuild via `scripts/build_food_catalog.py` (optional `--network` + `USDA_FDC_API_KEY`).
- **M2 choice:** ship a **~50KB** processed SQLite subset (`marrow/data/processed/foods_catalog.sqlite`, 13 foods from checked-in fixtures: 5 USDA, 3 OFF, 5 IFCT-style rows). Same schema as the user DB food tables; scale up by pointing the build script at downloaded raw files under `marrow/data/ingest/cache/` (gitignored).

## 2025-10-07 — M2 food catalog & ingestion

### Unified food schema (migration `002_food_catalog.sql`)

- Tables: `foods`, `food_nutrients`, `food_servings`.
- Nutrients are **wide columns** per 100 g or 100 ml (macros + micronutrients); `NULL` when a source does not provide a value.
- Metadata: `source` (`usda` | `off` | `ifct` | `sample`), `preparation` (`raw` | `cooked` | `unknown`), `data_quality` (`high` | `medium` | `low` | `estimated`), optional `brand` / `barcode` / `locale`.
- Canonical nutrient IDs and OFF key mapping live in `marrow/data/foods/nutrients.py` (single source of truth with the SQL migration).

### Ingestion layout

- `marrow/data/ingest/` — parsers (`usda.py`, `off.py`, `ifct.py`), `normalize.py`, `catalog.py`, `download.py`, `build.py`.
- `marrow/data/ingest/fixtures/` — small committed samples for offline CI and demo builds.
- `scripts/build_food_catalog.py` — CLI wrapper to regenerate the bundled catalog.

### Catalog vs user database

- **User DB** (`marrow.db` in AppData): migrations create empty food tables; diary/search (M3+) will attach or import from the bundled catalog.
- **Bundled catalog**: read-only dev/demo subset in the repo; not the live user database.

## 2025-10-07 — M3 food search, servings, custom foods & recipes

### Catalog seeding (user DB)

- On connect, after migrations, `ensure_catalog_seeded()` copies rows from `foods_catalog.sqlite` when the bundle file digest changes (`app_meta.foods_catalog_seed_digest`).
- Catalog sources (`usda`, `off`, `ifct`, `sample`) merge by `(source, source_food_id)`; user `custom` foods are never overwritten.

### FTS5 (`003_food_search.sql`)

- `foods_fts` uses `content='foods'` with insert/update/delete triggers; prefix queries via `unicode61` tokenizer.
- Search API returns BM25 rank and timing for dev profiling (&lt;100ms target on full catalog).

### Serving conversion

- `marrow/data/foods/units.py` — mass, volume, and household units (cup, tbsp, roti, katori, etc.); food-specific rows from `food_servings` when they match; approximate raw↔cooked factors for named staples.

### Custom foods & recipes

- `source='custom'` on `foods` for user entries (per 100g / 100ml nutrients).
- `recipes` + `recipe_ingredients`; per-serving nutrients computed by summing scaled ingredient macros.
- `food_favorites` and `food_recents` tables (write paths in M4 diary).
