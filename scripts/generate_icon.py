#!/usr/bin/env python3
"""Generate assets/marrow.ico for Windows builds."""

from __future__ import annotations

from pathlib import Path

try:
    from PIL import Image, ImageDraw
except ImportError as exc:
    raise SystemExit("Install Pillow: pip install pillow") from exc

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "marrow.ico"


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    size = 256
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    margin = 24
    draw.ellipse(
        (margin, margin, size - margin, size - margin),
        fill=(232, 168, 124, 255),
        outline=(212, 149, 106, 255),
        width=4,
    )
    draw.ellipse(
        (size * 0.32, size * 0.28, size * 0.68, size * 0.72),
        fill=(13, 13, 15, 220),
    )
    draw.text((size * 0.38, size * 0.36), "M", fill=(232, 168, 124, 255))

    sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    icons = [img.resize(s, Image.Resampling.LANCZOS) for s in sizes]
    icons[0].save(OUT, format="ICO", sizes=[(s[0], s[1]) for s in sizes])
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
