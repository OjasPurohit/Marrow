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

- Not in M1. Future food datasets will ship via a download script or Git LFS; documented here when chosen.
