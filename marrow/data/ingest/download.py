"""Optional network fetch for ingestion (raw cache only; never committed)."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

DEFAULT_CACHE = Path(__file__).resolve().parent / "cache"


def cache_dir() -> Path:
    override = os.environ.get("MARROW_INGEST_CACHE")
    path = Path(override) if override else DEFAULT_CACHE
    path.mkdir(parents=True, exist_ok=True)
    return path


def fetch_usda_foods_by_ids(
    fdc_ids: list[int],
    *,
    api_key: str | None = None,
    out_path: Path | None = None,
) -> Path:
    """Download individual FDC food documents and wrap as a minimal FoundationFoods JSON."""
    key = api_key or os.environ.get("USDA_FDC_API_KEY") or "DEMO_KEY"
    foods: list[dict] = []
    for fdc_id in fdc_ids:
        url = f"https://api.nal.usda.gov/fdc/v1/food/{fdc_id}?api_key={urllib.parse.quote(key)}"
        req = urllib.request.Request(url, headers={"User-Agent": "Marrow/0.1 (food ingest)"})
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                foods.append(json.loads(resp.read().decode("utf-8")))
        except urllib.error.HTTPError as exc:
            if exc.code == 403 and key == "DEMO_KEY":
                raise RuntimeError(
                    "USDA API rejected DEMO_KEY; set USDA_FDC_API_KEY for live downloads"
                ) from exc
            raise

    payload = {"FoundationFoods": foods}
    dest = out_path or (cache_dir() / "usda_api_foods.json")
    dest.write_text(json.dumps(payload), encoding="utf-8")
    return dest


def fetch_off_search(
    query: str,
    *,
    page_size: int = 5,
    out_path: Path | None = None,
) -> Path:
    """Fetch a small OFF search result set as JSONL (one product per line)."""
    params = urllib.parse.urlencode(
        {
            "search_terms": query,
            "search_simple": 1,
            "action": "process",
            "json": 1,
            "page_size": page_size,
        }
    )
    url = f"https://world.openfoodfacts.org/cgi/search.pl?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": "Marrow/0.1 (food ingest)"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    products = data.get("products") or []
    dest = out_path or (cache_dir() / f"off_search_{query.replace(' ', '_')}.jsonl")
    with dest.open("w", encoding="utf-8") as fh:
        for product in products:
            fh.write(json.dumps(product, ensure_ascii=False) + "\n")
    return dest
