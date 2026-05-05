"""Run all scrapers, normalize, validate, and write CSVs."""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional

from ..config import (
    LOG_DIR,
    OUTPUT_CSV,
    REVIEW_QUEUE_CSV,
    Settings,
    ensure_output_dirs,
    load_settings,
)
from ..normalizer import to_records
from ..scrapers import ScraperContext, build_scrapers
from ..schema import IncentiveRecord, RawIncentive
from ..validators.completeness import enforce_review_flags
from ..validators.sanity import verify_links
from .dedupe import dedupe
from .writer import write_records, write_review_queue

LOGGER = logging.getLogger(__name__)


def run_pipeline(
    sources: Optional[Iterable[str]] = None,
    *,
    settings: Optional[Settings] = None,
    output_path: Path = OUTPUT_CSV,
    review_path: Path = REVIEW_QUEUE_CSV,
    log_dir: Path = LOG_DIR,
    check_links: int = 0,
) -> List[IncentiveRecord]:
    """Execute every scraper and write the final CSV.

    Returns the in-memory list of records so callers (and tests) can inspect
    them without re-reading the file.
    """

    ensure_output_dirs()
    settings = settings or load_settings()
    ctx = ScraperContext(
        settings=settings,
        session=__lazy_session(),
        llm=__lazy_llm(settings),
    )

    scrapers = build_scrapers(sources, ctx=ctx)
    LOGGER.info("running %d scrapers", len(scrapers))

    raw: List[RawIncentive] = []
    audit: List[dict] = []
    for scraper in scrapers:
        t0 = time.monotonic()
        try:
            results = scraper.run()
        except Exception as exc:  # pragma: no cover - defensive
            LOGGER.exception("scraper %s crashed: %s", scraper.key, exc)
            results = []
        elapsed = time.monotonic() - t0
        audit.append(
            {
                "scraper": scraper.key,
                "name": scraper.name,
                "count": len(results),
                "elapsed_s": round(elapsed, 2),
            }
        )
        raw.extend(results)

    LOGGER.info("collected %d raw records before dedupe", len(raw))
    raw = dedupe(raw)
    LOGGER.info("%d raw records after dedupe", len(raw))

    normalized = to_records(raw)
    normalized = enforce_review_flags(normalized)
    normalized = verify_links(normalized, max_checks=check_links)

    write_records(output_path, normalized)
    write_review_queue(review_path, normalized)

    log_dir.mkdir(parents=True, exist_ok=True)
    audit_path = log_dir / f"run_{datetime.now().strftime('%Y%m%dT%H%M%S')}.jsonl"
    with audit_path.open("w", encoding="utf-8") as fh:
        for line in audit:
            fh.write(json.dumps(line) + "\n")
    LOGGER.info("audit written to %s", audit_path)

    return normalized


# ---------------------------------------------------------------------------
# Lazy helpers (split out so tests can patch easily)
# ---------------------------------------------------------------------------


def __lazy_session():
    from ..extractors.http import get_session

    return get_session()


def __lazy_llm(settings: Settings):
    from ..parsers.llm_parser import LLMParser

    return LLMParser(settings=settings)
