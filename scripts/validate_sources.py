#!/usr/bin/env python3
"""Validate that every URL in sources.py responds (HEAD with GET fallback).

Usage:
    PYTHONPATH=src python scripts/validate_sources.py
    PYTHONPATH=src python scripts/validate_sources.py --csv output/.../extracted_tampa_incentives.csv
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

# Allow running without an editable install.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from urllib.parse import urlparse

from dreamline_scraper.extractors.http import get_session  # noqa: E402
from dreamline_scraper.sources import SOURCES  # noqa: E402

# Hosts that routinely time out on HEAD but work via Playwright in the pipeline.
_WARN_ONLY_HOSTS = {"www.rd.usda.gov"}


def check_url(session, url: str) -> bool:
    return session.head_ok(url)


def _warn_only(url: str) -> bool:
    return urlparse(url).netloc in _WARN_ONLY_HOSTS


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate configured source URLs.")
    parser.add_argument(
        "--csv",
        type=Path,
        help="Also check unique program_links values in a produced CSV.",
    )
    args = parser.parse_args()

    session = get_session()
    failed: list[str] = []
    warned: list[str] = []

    print(f"Checking {len(SOURCES)} sources in sources.py …")
    for source in SOURCES:
        ok = check_url(session, source.url)
        if ok:
            status = "OK"
        elif _warn_only(source.url):
            status = "WARN"
            warned.append(f"source: {source.name} -> {source.url}")
        else:
            status = "FAIL"
            failed.append(f"source: {source.name} -> {source.url}")
        print(f"  [{status}] {source.name}")

    if args.csv and args.csv.exists():
        seen: set[str] = set()
        with args.csv.open(newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                link = (row.get("program_links") or "").strip()
                if link and link not in seen:
                    seen.add(link)
        print(f"\nChecking {len(seen)} unique program_links in {args.csv} …")
        for link in sorted(seen):
            ok = check_url(session, link)
            status = "OK" if ok else "FAIL"
            print(f"  [{status}] {link[:90]}")
            if not ok:
                failed.append(f"program_links: {link}")

    if warned:
        print(f"\n{len(warned)} URL(s) timed out or blocked HEAD (fetch via Playwright):")
        for item in warned:
            print(f"  - {item}")

    if failed:
        print(f"\n{len(failed)} URL(s) failed liveness checks:")
        for item in failed:
            print(f"  - {item}")
        return 1

    print("\nAll required source URLs responded (warnings may still be listed).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
