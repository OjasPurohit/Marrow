#!/usr/bin/env python3
"""CLI entry: build the bundled foods catalog SQLite subset."""

from marrow.data.ingest.build import main

if __name__ == "__main__":
    raise SystemExit(main())
