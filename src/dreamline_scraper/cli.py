"""Command-line interface."""

from __future__ import annotations

import argparse
import logging
import sys
from typing import List, Optional

from .config import OUTPUT_CSV, REVIEW_QUEUE_CSV, SOURCE_KEYS, load_settings
from .pipeline.orchestrator import run_pipeline


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="dreamline-scraper",
        description=(
            "Scrape Tampa / Hillsborough incentive programs and write the "
            "extracted_tampa_incentives.csv deliverable."
        ),
    )
    p.add_argument(
        "command",
        choices=["run", "list-sources"],
        help="Action to perform.",
    )
    p.add_argument(
        "--source",
        action="append",
        dest="sources",
        choices=SOURCE_KEYS,
        help="Limit to one or more source keys (repeatable). Default: all sources.",
    )
    p.add_argument(
        "--output",
        default=str(OUTPUT_CSV),
        help=f"Output CSV path. Default: {OUTPUT_CSV}",
    )
    p.add_argument(
        "--review-queue",
        default=str(REVIEW_QUEUE_CSV),
        help=f"Review queue CSV path. Default: {REVIEW_QUEUE_CSV}",
    )
    p.add_argument(
        "--check-links",
        type=int,
        default=0,
        help=(
            "If non-zero, HEAD-check program_links and flag broken URLs for "
            "review. Pass -1 to check every record (slow). Default: 0 (skip)."
        ),
    )
    p.add_argument(
        "--disable-curated",
        action="store_true",
        help=(
            "Suppress every scraper's hardcoded curated baseline. Use this "
            "to see exactly what the live scrapers / APIs / LLM parser "
            "produce on their own."
        ),
    )
    p.add_argument(
        "--include-source",
        action="store_true",
        help=(
            "Append an extraction_source column to the deliverable CSV so "
            "callers can see whether each row came from live / api / llm / "
            "curated extraction."
        ),
    )
    p.add_argument("-v", "--verbose", action="count", default=0)
    return p


def main(argv: Optional[List[str]] = None) -> int:
    args = _parser().parse_args(argv)
    level = logging.WARNING - 10 * min(args.verbose, 2)
    logging.basicConfig(level=level, format="%(levelname)s %(name)s: %(message)s")

    if args.command == "list-sources":
        from .config import SOURCES
        for s in SOURCES:
            print(f"{s.priority}\t{s.key}\t{s.name}")
        return 0

    settings = load_settings()
    if args.disable_curated:
        settings.disable_curated = True
    records = run_pipeline(
        sources=args.sources,
        settings=settings,
        output_path=__path(args.output),
        review_path=__path(args.review_queue),
        check_links=args.check_links,
        include_source=args.include_source,
    )
    flagged = sum(1 for r in records if r.review_needed == "Yes")
    # Provenance breakdown so the operator sees live vs curated vs llm at a glance.
    from collections import Counter
    counts = Counter(r.extraction_source or "unknown" for r in records)
    breakdown = ", ".join(f"{k}={v}" for k, v in sorted(counts.items())) or "empty"
    print(
        f"Wrote {len(records)} records to {args.output} "
        f"({flagged} flagged for review). Sources: {breakdown}"
    )
    return 0


def __path(value: str):
    from pathlib import Path

    return Path(value)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
