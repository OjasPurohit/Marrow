# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec — single-file Marrow desktop build."""

import sys
from pathlib import Path

block_cipher = None
ROOT = Path(SPECPATH).resolve().parent

datas = [
    (str(ROOT / "ui" / "dist"), "ui/dist"),
    (str(ROOT / "marrow" / "data" / "migrations"), "marrow/data/migrations"),
    (
        str(ROOT / "marrow" / "data" / "processed" / "foods_catalog.sqlite"),
        "marrow/data/processed",
    ),
]

icon_path = ROOT / "assets" / "marrow.ico"
icon = str(icon_path) if icon_path.is_file() else None

version_file = ROOT / "assets" / "version_info.txt"
version = str(version_file) if sys.platform == "win32" and version_file.is_file() else None

hiddenimports = [
    "webview",
    "keyring.backends",
    "keyring.backends.fail",
    "keyring.backends.chainer",
    "keyring.backends.SecretService",
    "keyring.backends.Windows",
    "keyring.backends.macOS",
    "sqlite3",
]

a = Analysis(
    [str(ROOT / "marrow" / "main.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="Marrow",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon,
    version=version,
)
