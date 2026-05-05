"""End-to-end smoke test that runs the full pipeline against the curated
fallbacks (no live network) and asserts the CSV column order + row schema."""

from __future__ import annotations

import csv
from pathlib import Path

from dreamline_scraper.config import Settings
from dreamline_scraper.pipeline.orchestrator import run_pipeline
from dreamline_scraper.schema import CSV_COLUMNS, IncentiveType


def test_pipeline_writes_csv_in_required_order(tmp_path: Path, monkeypatch):
    # Force every scraper to use its curated fallback by disabling network
    # I/O at the session level.

    from dreamline_scraper.scrapers.dsire_florida import DSIREFloridaScraper
    monkeypatch.setattr(DSIREFloridaScraper, "_scrape_live", lambda self: iter([]))

    from dreamline_scraper.parsers.llm_parser import LLMParser
    monkeypatch.setattr(LLMParser, "enabled", property(lambda self: False))

    out = tmp_path / "incentives.csv"
    review = tmp_path / "review_queue.csv"
    log_dir = tmp_path / "logs"

    settings = Settings()
    records = run_pipeline(
        settings=settings,
        output_path=out,
        review_path=review,
        log_dir=log_dir,
    )

    assert out.exists(), "Expected CSV output file to be written"
    assert review.exists(), "Expected review queue file to be written"

    # Verify header + column order + at least 1 row
    with out.open() as fh:
        reader = csv.reader(fh)
        header = next(reader)
        rows = list(reader)
    assert header == CSV_COLUMNS
    assert rows, "CSV must contain at least one record"

    valid_types = {t.value for t in IncentiveType}
    for row in rows:
        assert len(row) == len(CSV_COLUMNS)
        assert row[CSV_COLUMNS.index("incentive_type")] in valid_types
        assert row[CSV_COLUMNS.index("program_name")].strip()
        assert row[CSV_COLUMNS.index("program_links")].startswith("http")
        assert row[CSV_COLUMNS.index("review_needed")] in {"Yes", "No"}

    assert len(records) >= 20, (
        f"expected at least 20 curated records, got {len(records)}"
    )
