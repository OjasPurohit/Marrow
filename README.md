# Marrow

Premium offline-first diet and nutrition tracker for Windows students — desktop shell via pywebview + Edge WebView2, Svelte UI, local SQLite.

## Features

- **Today** — Quick natural-language log, meal groups, macro rings, timeline, optional photo log (Groq vision)
- **Foods** — FTS5 search over bundled catalog, custom foods, recipes, serving conversion
- **Night review** — Full-day micro report, flags vs targets, optional Groq summary
- **History** — Month heatmap, streaks, drill-down to any day
- **Trends** — 7/30/90-day intake, balance, micronutrients, weight log with smoothed trend
- **Profile & onboarding** — Mifflin-St Jeor targets, deficit/surplus, micronutrient goals
- **Settings** — Theme, units, UI scale, accessibility (motion/transparency/contrast), backup/export, command palette (`Ctrl+K`)
- **Optional Groq** — API key in OS keyring: smarter parse, dish decomposition, Whisper voice hotkey, night summary

## Requirements

### End users (Windows)

- **Windows 10/11** with [Microsoft Edge WebView2](https://developer.microsoft.com/microsoft-edge/webview2/) runtime
- Download **`Marrow.exe`** from [GitHub Releases](https://github.com/OjasPurohit/Marrow/releases) (v1.0.0+), or build locally (below)

User data lives under `%LOCALAPPDATA%\Marrow\` (database, config, rotating backups). Never commit your DB or API keys.

### Developers

- **Python 3.11+**
- **Node.js 20+** (UI build)
- **Microsoft Edge WebView2** (Windows production); Linux/macOS use GTK/WebKit or Cocoa for local dev

## Install (development)

```bash
git clone https://github.com/OjasPurohit/Marrow.git
cd Marrow
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt

cd ui && npm ci && cd ..
```

## Quick start (development)

```bash
# Terminal 1 — Vite dev server
cd ui && npm run dev

# Terminal 2 — Desktop shell (loads http://127.0.0.1:5173)
export MARROW_DEV=1   # Windows: set MARROW_DEV=1
python -m marrow.main
```

## Production UI (without PyInstaller)

```bash
cd ui && npm run build && cd ..
python -m marrow.main
```

Without `MARROW_DEV`, the shell loads bundled `ui/dist/index.html`.

## Windows release build (PyInstaller)

On **Windows** (recommended for shipping `Marrow.exe`):

```bat
build.bat
```

Or cross-platform:

```bash
python scripts/build_release.py
```

This runs `npm run build` in `ui/`, then PyInstaller using `scripts/marrow.spec`, producing:

- **Windows:** `dist/Marrow.exe` (single file, windowed, icon + version metadata)
- **Other platforms:** `dist/Marrow` (smoke-test only; ship Windows `.exe` for students)

Optional voice hotkey at runtime: `pip install sounddevice pynput` (not required for core logging).

### Performance notes

- **Startup:** SQLite migrations + catalog seed run once on first connect; automatic backup is capped at one per calendar day.
- **Food search:** FTS5 prefix search; dev UI shows query time in ms. On the bundled ~13-food demo catalog, searches are sub-millisecond; with a full rebuilt catalog, expect **&lt;100 ms** on typical student laptops (see M3 decision in [docs/DECISIONS.md](docs/DECISIONS.md)).

## Tests

```bash
pytest
cd ui && npm test
```

## Screenshots

| Screen | Path |
|--------|------|
| Today | [docs/screenshots/today.png](docs/screenshots/today.png) *(add on Windows)* |
| Night review | [docs/screenshots/night-review.png](docs/screenshots/night-review.png) |
| History | [docs/screenshots/history.png](docs/screenshots/history.png) |
| Settings | [docs/screenshots/settings.png](docs/screenshots/settings.png) |

See [docs/screenshots/README.md](docs/screenshots/README.md) for capture steps.

## Data sources & licenses

Marrow ships a **small processed subset** of public food data for offline demo/CI (`marrow/data/processed/foods_catalog.sqlite`). Full dumps are not redistributed in git.

| Source | Use in Marrow | License / terms |
|--------|----------------|-----------------|
| [USDA FoodData Central](https://fdc.nal.usda.gov/) | Foundation-style nutrients via ingest pipeline | [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/) (USDA FDC) |
| [Open Food Facts](https://world.openfoodfacts.org/) | Barcode / branded rows when you rebuild catalog | [ODbL 1.0](https://opendatacommons.org/licenses/odbl/) — share-alike if you republish derived DBs |
| IFCT-style CSV | Indian food reference rows in fixtures | Treat as reference data; verify license for your own full IFCT imports |

Regenerate a larger catalog locally:

```bash
python3 scripts/build_food_catalog.py
# optional network (USDA API key):
USDA_FDC_API_KEY=... python3 scripts/build_food_catalog.py --network
```

Raw downloads go to `marrow/data/ingest/cache/` (gitignored).

## Repository layout

```
marrow/           Python package (core, data, services, bridge)
ui/               Svelte + Vite frontend
scripts/          Catalog build, PyInstaller spec, release build
assets/           App icon + Windows version info
docs/             Decisions, screenshot placeholders
tests/            pytest
build.bat         Windows one-shot release build
```

## Roadmap

| Milestone | Status | Notes |
|-----------|--------|-------|
| **M1** Scaffold | Done | pywebview shell, bridge, SQLite migrations, Svelte UI tokens |
| **M1b** Design lab | Done | Dev-only component gallery + interaction lab (`#/gallery`) |
| **M2** Food ingestion | Done | Unified schema, ingest pipeline, bundled catalog subset |
| **M3** Food search | Done | FTS5 search, serving conversion, custom foods & recipes |
| **M4** NL parser & diary | Done | Rule-based parse, confirmation UI, diary schema |
| **M5** Today & totals | Done | Rings/bars, meal groups, timeline, daily aggregation |
| **M6** Goals & onboarding | Done | Mifflin-St Jeor, DB targets, deficit/surplus, weight log |
| **M7** Night review | Done | Full-day micro report, flags, rule summary |
| **M8** Groq (optional) | Done | Keyring API key, voice, photo, night summary |
| **M9** History & trends | Done | Heatmap, trend charts, weight log |
| **M10** Settings & backup | Done | Palette, export, a11y prefs, photo log |
| **M11** Polish & v1.0.0 | Done | PyInstaller `Marrow.exe`, empty states, README, release |

Decisions: [docs/DECISIONS.md](docs/DECISIONS.md).

## Remote

`https://github.com/OjasPurohit/Marrow` — `main` branch.
