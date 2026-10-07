"""Orchestrate catalog build from fixtures and optional downloads."""

from __future__ import annotations

import argparse
from pathlib import Path

from marrow.data.ingest.catalog import catalog_stats, open_catalog, upsert_foods
from marrow.data.ingest.download import fetch_off_search, fetch_usda_foods_by_ids
from marrow.data.ingest.ifct import iter_ifct_from_fixture_dir
from marrow.data.ingest.off import iter_off_from_fixture_dir
from marrow.data.ingest.usda import iter_usda_from_fixture_dir, load_usda_json_path
from marrow.core.paths import bundled_foods_catalog_path

FIXTURES = Path(__file__).resolve().parent / "fixtures"

# Small curated FDC ids (foundation / sr legacy) for optional live refresh
DEFAULT_USDA_FDC_IDS = [173944, 171688, 174259, 168462, 169738]


def collect_records(
    *,
    use_network: bool = False,
    usda_ids: list[int] | None = None,
    off_queries: list[str] | None = None,
) -> list:
    from marrow.data.ingest.models import FoodRecord

    records: list[FoodRecord] = []
    records.extend(iter_usda_from_fixture_dir(FIXTURES / "usda"))
    records.extend(iter_off_from_fixture_dir(FIXTURES / "off"))
    records.extend(iter_ifct_from_fixture_dir(FIXTURES / "ifct"))

    if use_network:
        ids = usda_ids or DEFAULT_USDA_FDC_IDS
        usda_path = fetch_usda_foods_by_ids(ids)
        records.extend(load_usda_json_path(usda_path))
        from marrow.data.ingest.off import load_off_jsonl

        for query in off_queries or ["oats", "yogurt"]:
            off_path = fetch_off_search(query, page_size=3)
            records.extend(load_off_jsonl(off_path))

    # De-dupe by (source, source_food_id) keeping last
    deduped: dict[tuple[str, str], FoodRecord] = {}
    for rec in records:
        deduped[(rec.source, rec.source_food_id)] = rec
    return list(deduped.values())


def build_catalog(
    output: Path | None = None,
    *,
    use_network: bool = False,
) -> dict:
    dest = output or bundled_foods_catalog_path()
    records = collect_records(use_network=use_network)
    conn = open_catalog(dest)
    try:
        upsert_foods(conn, records)
        stats = catalog_stats(conn)
    finally:
        conn.close()
    stats["path"] = str(dest)
    stats["bytes"] = dest.stat().st_size
    return stats


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build Marrow offline foods catalog SQLite")
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output SQLite path (default: marrow/data/processed/foods_catalog.sqlite)",
    )
    parser.add_argument(
        "--network",
        action="store_true",
        help="Fetch supplemental USDA/OFF rows into ingest cache (requires USDA_FDC_API_KEY)",
    )
    args = parser.parse_args(argv)
    stats = build_catalog(args.output, use_network=args.network)
    print(
        f"Wrote {stats['foods']} foods ({stats['by_source']}) "
        f"→ {stats['path']} ({stats['bytes']} bytes)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
