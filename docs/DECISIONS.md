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

## 2025-10-07 — M4 natural-language log parser & confirmation

### Parser pipeline

1. **Local rule-based parser** (`marrow/services/food_text_parser.py`) — quantities (fractions, “2 and a half”, Hindi number words), units (g, katori, roti, …), Hinglish food aliases → FTS5 match.
2. **Groq slot** (`marrow/services/diary_parse.py`) — runs only when `GROQ_API_KEY` is set **and** local parse finds no foods; implementation deferred to **M8** (hook present, no network calls in M4).
3. **Confirmation UI** on Today (`#/`) before any diary write.

### Diary schema (migration `004_diary.sql`)

- `diary_logs` — `log_date`, `meal_tag` (`breakfast` | `lunch` | `dinner` | `snack`), optional `source_text`.
- `diary_log_entries` — portion, scaled macros (nullable), `match_confidence` (`EXACT` | `GOOD` | `ESTIMATED`).

### Bridge

- `parse_food_text`, `confirm_and_save_log`, `list_diary_entries_for_date`.

### Accuracy at confirmation

- Macro–kcal consistency warning (~10% tolerance) via `nutrient_validation.py`.
- Portion / per-item kcal sanity warnings; `NULL` nutrients stay `null` end-to-end (never coerced to 0 in API or UI display helpers).

## 2025-10-07 — M5 Today screen & daily totals

### Daily aggregation

- `marrow/services/diary_totals.py` — sum `energy_kcal`, `protein_g`, `carbs_g`, `fat_g` from persisted diary entries; **any NULL in a column makes that day’s total NULL** for that nutrient.
- `list_diary_entries_for_date` returns `meals` (grouped by `meal_tag`), `totals` (macros + `targets` + `remaining`), and flat `entries` for the timeline.
- `get_daily_nutrient_totals` bridge alias for the same payload shape (totals-focused clients).

### Placeholder budgets (until M6)

- Fixed defaults in `PLACEHOLDER_DAILY_TARGETS` (2200 kcal, 150 g protein, etc.); UI labels them as placeholders.

### Meal tags

- Migration `005_diary_workout_meal_tags.sql` adds `pre_workout` and `post_workout` to `diary_logs.meal_tag`.

### Today UI

- Hand-built SVG `NutrientRing` + `MacroBar` components using design tokens (no chart library).

## 2025-10-07 — M6 onboarding, targets & energy balance

### Metabolism

- **Mifflin-St Jeor** BMR in `marrow/services/metabolism.py`; TDEE = BMR × activity multiplier.
- Goals adjust TDEE: cut −400 kcal, maintain 0, lean bulk +250 kcal; **minimum intake guardrails** 1200 (female) / 1500 (male) with user-visible warnings.
- Default macro split: protein g/kg by goal, fat ~0.8 g/kg floor, remainder carbs.

### Schema (migration `006_profile_targets.sql`)

- Extended `user_profile` (demographics, goal, tolerance %, optional gym weekdays JSON).
- `daily_macro_targets` rows: `default`, `gym` (+200 kcal suggestion), `rest`.
- `micronutrient_targets` seeded from adult RDA defaults (`rda_defaults.py`), editable on save.
- `weight_log` for body-weight entries (trend UI deferred to M9).

### Daily status

- `classify_energy_balance` → `DEFICIT` | `ON_TARGET` | `SURPLUS` vs resolved day target; symmetric ±`calorie_tolerance_pct` band (default 5%).
- Today totals include `energy_balance` and DB-backed `targets` (placeholders only before onboarding completes).

### UI

- First-launch **onboarding** overlay (editable suggested macros, disclaimer acknowledgement).
- **Profile** nav route (`#/profile`) for read-only target summary until M10 settings.

## 2025-10-07 — M7 night review

### Aggregation

- `marrow/services/night_review.py` — scales full food nutrient panels per diary entry (`grams_equivalent`), sums with per-nutrient coverage (partial totals when some entries lack data).
- Macro totals for energy balance still use persisted diary entry macros (`diary_totals` NULL rules).
- Top food contributors per nutrient; rule-based `summary_lines`; `groq_summary` stub `null` for M8.

### Flags & confidence

- Low (&lt;70% of target) / high (&gt;120%, or upper-limit nutrients like sodium) vs macro + micronutrient targets.
- `estimated_confidence` — share of logged kcal from `match_confidence=ESTIMATED` entries.

### Bridge & UI

- `get_night_review(log_date?)` on the bridge.
- Route `#/night-review` (nav **Review**); hand-built SVG macro split + micro bars (`MacroSplitSvg`, `MicroBarSvg`).

## 2025-10-07 — M8 Groq integration (optional)

### Credentials & settings

- Groq API key stored with **python-keyring** (`Marrow` / `groq_api_key`); never written to `config.json`, SQLite, logs, or git.
- Non-secret Groq options live under `config.json` → `groq` (chat + Whisper model names, timeouts, retries, voice hotkey, night-summary toggle).
- `GROQ_API_KEY` env is supported for local dev/CI only; production path is keyring via bridge `set_groq_api_key` / `clear_groq_api_key`.

### Parser pipeline (4b)

1. **Local rule-based parser** unchanged (deterministic tests).
2. **Groq JSON parse** when keyring key is set **and** local pass matches no foods: temperature `0`, `response_format: json_object`, schema `{food_name, quantity, unit, meal}`; optional `dish` + `ingredients[{food_name, grams}]` for decomposition.
3. Nutrients always from DB (`convert_food_serving` / `aggregate_recipe_nutrients`); LLM output is never trusted for numbers.
4. On confirm, matched decompositions expand to per-ingredient diary rows and are **cached as recipes** (`create_recipe`).

### Voice (4c)

- Optional global hotkey (`groq.voice_hotkey`, default `ctrl+shift+v`) records WAV in Python (`sounddevice`) and transcribes via Groq Whisper; transcript is dispatched to the UI (`marrow-voice-transcript`) and reuses `parse_food_text`.
- Bridge: `transcribe_voice_note`, `poll_voice_transcript`; hotkey listener starts from `marrow.main` when configured.
- Graceful offline: network/HTTP errors skip Groq stages; local parser and rule-based night review still work.

### Night review

- Optional `groq_summary` prose from **computed totals and rule lines only** (`groq_night_summary.py`); disabled when key missing or `enable_night_summary` is false.

### Client

- `marrow/services/groq_client.py` — urllib transport, timeouts, retry on 429/5xx; injectable transport for pytest.

## 2025-10-07 — M9 history, trends & weight log

### History

- `marrow/services/diary_history.py` — range and month payloads with per-day macro totals (NULL rules from `diary_totals`), energy balance, `logged` / `data_incomplete` flags, streak counters.
- UI `#/history` — month calendar heatmap (balance-colored), recent day list; day drill-down reuses `#/night-review?date=YYYY-MM-DD`.

### Trends

- `marrow/services/trends.py` — 7 / 30 / 90-day series for calories, protein, energy delta, rolling 7-day intake and balance averages, optional micronutrient keys (scaled panels via night-review helpers), weight points + smoothed line, ISO-week average balance with cumulative weekly balance.
- UI `#/trends` — hand-built SVG `TrendLineSvg`, micronutrient chip picker (from profile targets), weight entry form and list.

### Weight bridge

- `delete_weight_entry`, `get_weight_log_with_trend` (7-day trailing moving average); existing `add_weight_entry` / `list_weight_entries` unchanged.

### Bridge

- `get_diary_history_range`, `get_diary_history_month`, `get_trend_series`.
