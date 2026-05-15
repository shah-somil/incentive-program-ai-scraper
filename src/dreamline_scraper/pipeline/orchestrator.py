"""Source-driven pipeline: fetch each page, LLM-parse, validate, write CSV."""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Callable, Iterable, List, Optional

from ..config import (
    LOG_DIR,
    OUTPUT_CSV,
    REVIEW_QUEUE_CSV,
    Settings,
    ensure_output_dirs,
    load_settings,
)
from ..extractors.fetch import FetchResult, fetch
from ..extractors.http import get_session
from ..normalizer import to_records
from ..parsers.llm_parser import LLMParser
from ..schema import IncentiveRecord, RawIncentive
from ..sources import SOURCES, Source
from ..validators.completeness import enforce_review_flags
from ..validators.sanity import verify_links
from .dedupe import dedupe
from .writer import write_records, write_review_queue

LOGGER = logging.getLogger(__name__)


Fetcher = Callable[[Source], FetchResult]


def run_pipeline(
    source_names: Optional[Iterable[str]] = None,
    *,
    settings: Optional[Settings] = None,
    output_path: Path = OUTPUT_CSV,
    review_path: Path = REVIEW_QUEUE_CSV,
    log_dir: Path = LOG_DIR,
    check_links: int = 0,
    include_source: bool = False,
    fetcher: Optional[Fetcher] = None,
    llm: Optional[LLMParser] = None,
) -> List[IncentiveRecord]:
    """Fetch every source, LLM-parse, validate, write CSVs.

    ``source_names`` filters the registry to a subset (matched on
    ``Source.name`` substring, case-insensitive).  Pass ``fetcher`` / ``llm``
    to inject test doubles.
    """

    ensure_output_dirs()
    settings = settings or load_settings()

    sources = _select_sources(source_names)
    if not sources:
        LOGGER.warning("no sources selected")
        return []

    session = get_session()
    fetcher = fetcher or (
        lambda s: fetch(
            s.url,
            render=s.render,
            wait_selector=s.wait_selector,
            timeout_ms=s.timeout_ms,
            session=session,
        )
    )
    llm = llm or LLMParser(settings=settings)

    if not llm.enabled:
        LOGGER.warning(
            "OPENAI_API_KEY not set — LLM parser disabled; "
            "the pipeline will return zero records."
        )

    raw: List[RawIncentive] = []
    audit: List[dict] = []
    for source in sources:
        t0 = time.monotonic()
        try:
            result = fetcher(source)
        except Exception as exc:
            LOGGER.exception("fetch crashed for %s: %s", source.name, exc)
            result = FetchResult(text="", content_type="empty", final_url=source.url)

        records: List[RawIncentive] = []
        if result.text:
            try:
                records = llm.parse(
                    content=result.text,
                    source=source,
                    final_url=result.final_url,
                    content_type=result.content_type,
                )
            except Exception as exc:
                LOGGER.exception("llm parse crashed for %s: %s", source.name, exc)
        elapsed = time.monotonic() - t0

        audit.append(
            {
                "source": source.name,
                "url": source.url,
                "level": source.level,
                "content_type": result.content_type,
                "text_chars": len(result.text or ""),
                "records": len(records),
                "elapsed_s": round(elapsed, 2),
            }
        )
        LOGGER.info(
            "%s -> %d records (%s, %d chars, %.1fs)",
            source.name,
            len(records),
            result.content_type,
            len(result.text or ""),
            elapsed,
        )
        raw.extend(records)

    LOGGER.info("collected %d raw records before dedupe", len(raw))
    raw = dedupe(raw)
    LOGGER.info("%d raw records after dedupe", len(raw))

    normalized = to_records(raw)
    normalized = enforce_review_flags(normalized)
    normalized = verify_links(normalized, max_checks=check_links)

    write_records(output_path, normalized, include_source=include_source)
    write_review_queue(review_path, normalized)

    log_dir.mkdir(parents=True, exist_ok=True)
    audit_path = log_dir / f"run_{datetime.now().strftime('%Y%m%dT%H%M%S')}.jsonl"
    with audit_path.open("w", encoding="utf-8") as fh:
        for line in audit:
            fh.write(json.dumps(line) + "\n")
    LOGGER.info("audit written to %s", audit_path)

    return normalized


def _select_sources(names: Optional[Iterable[str]]) -> List[Source]:
    if not names:
        return list(SOURCES)
    wanted = [n.lower() for n in names]
    return [s for s in SOURCES if any(w in s.name.lower() for w in wanted)]
