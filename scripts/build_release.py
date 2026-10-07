#!/usr/bin/env python3
"""Build production UI and PyInstaller single-file executable."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UI = ROOT / "ui"
DIST = ROOT / "dist"
SPEC = ROOT / "scripts" / "marrow.spec"


def run(cmd: list[str], cwd: Path | None = None) -> None:
    print("+", " ".join(cmd))
    subprocess.run(cmd, cwd=cwd or ROOT, check=True)


def main() -> int:
    if not (UI / "package.json").is_file():
        print("ui/package.json missing", file=sys.stderr)
        return 1

    icon = ROOT / "assets" / "marrow.ico"
    if not icon.is_file():
        run([sys.executable, str(ROOT / "scripts" / "generate_icon.py")])

    dist_index = UI / "dist" / "index.html"
    if os.environ.get("MARROW_FORCE_UI_BUILD") or not dist_index.is_file():
        npm = "npm.cmd" if sys.platform == "win32" else "npm"
        if not (UI / "node_modules").is_dir():
            run([npm, "ci"], cwd=UI)
        run([npm, "run", "build"], cwd=UI)

    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        run([sys.executable, "-m", "pip", "install", "pyinstaller>=6.0"])

    if DIST.exists():
        shutil.rmtree(DIST)
    run([sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", str(SPEC)])

    built = DIST / ("Marrow.exe" if sys.platform == "win32" else "Marrow")
    if built.is_file():
        print(f"Built {built}")
    else:
        print("PyInstaller finished but executable not found", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
