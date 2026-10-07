# Marrow

Premium offline-first diet and nutrition tracker for Windows (desktop shell via pywebview + Edge WebView2).

## Requirements

- **Python 3.11+**
- **Node.js 20+** (for UI build)
- **Microsoft Edge WebView2** runtime (Windows production)
- Linux/macOS: pywebview uses GTK/WebKit or Cocoa for local dev

## Quick start (development)

```bash
# Python backend
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt

# Frontend
cd ui && npm install && cd ..

# Terminal 1 — Vite dev server
cd ui && npm run dev

# Terminal 2 — Desktop shell (loads http://127.0.0.1:5173)
export MARROW_DEV=1
python -m marrow.main
```

User data (SQLite DB, window geometry) is stored under:

- Windows: `%LOCALAPPDATA%\Marrow\`
- Linux: `~/.local/share/Marrow/`
- macOS: `~/Library/Application Support/Marrow/`

Never commit the database or secrets.

## Production UI build

```bash
cd ui && npm run build && cd ..
python -m marrow.main
```

Without `MARROW_DEV`, the shell loads `ui/dist/index.html`.

## Tests

```bash
pytest
cd ui && npm test
```

## Repository layout

```
marrow/           Python package (core, data, services, bridge)
ui/               Svelte + Vite frontend
docs/             Product & architecture decisions
tests/            pytest
```

## Roadmap

| Milestone | Status | Notes |
|-----------|--------|-------|
| **M1** Scaffold | Done | pywebview shell, bridge, SQLite migrations, Svelte UI tokens |
| **M1b** Design lab | Done | Dev-only component gallery + interaction lab (`#/gallery`) |
| **M2** Food ingestion | Planned | USDA / Open Food Facts pipeline, search UI |
| **M3** Diary & meals | Planned | Logging, portions, daily totals |
| **M4+** Goals, charts, sync | Planned | See project spec |

Decisions are logged in [docs/DECISIONS.md](docs/DECISIONS.md).

## Remote

`https://github.com/OjasPurohit/Marrow` — `main` branch.
