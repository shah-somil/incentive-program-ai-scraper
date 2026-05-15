"""End-to-end smoke test with a stub fetcher + stub LLM parser."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import List

from dreamline_scraper.config import Settings
from dreamline_scraper.extractors.fetch import FetchResult
from dreamline_scraper.parsers.llm_parser import LLMParser
from dreamline_scraper.pipeline.orchestrator import run_pipeline
from dreamline_scraper.schema import CSV_COLUMNS, IncentiveType, RawIncentive
from dreamline_scraper.sources import Source


class _StubLLM(LLMParser):
    """LLM stand-in that returns one record per source without hitting OpenAI."""

    def __init__(self):
        super().__init__(settings=Settings(openai_api_key="sk-stub"))

    @property
    def enabled(self) -> bool:
        return True

    def parse(self, *, content, source: Source, final_url, content_type, max_chars=16000):
        return [
            RawIncentive(
                program_name=f"{source.name} program",
                level=source.level,
                state=source.state or None,
                county=source.county or None,
                city=source.city or None,
                utility_provider=source.utility or None,
                type="rebate",
                amount_type="up_to",
                amount_value=1000,
                amount_text="up to $1,000",
                description=f"Test record extracted from {source.name}.",
                eligibility_notes="Owner-occupied properties only.",
                source_url=final_url or source.url,
                application_url=source.url,
                expires_at="2030-12-31",
                confidence_score=0.85,
                extraction_source="llm",
            )
        ]


def _stub_fetcher(source: Source) -> FetchResult:
    return FetchResult(
        text=f"Pretend this is the body of {source.name} with a $1,000 rebate.",
        content_type="html_text",
        final_url=source.url,
    )


def test_pipeline_writes_csv_in_required_order(tmp_path: Path):
    out = tmp_path / "incentives.csv"
    review = tmp_path / "review_queue.csv"
    log_dir = tmp_path / "logs"

    records = run_pipeline(
        settings=Settings(),
        output_path=out,
        review_path=review,
        log_dir=log_dir,
        fetcher=_stub_fetcher,
        llm=_StubLLM(),
    )

    assert out.exists()
    assert review.exists()
    assert log_dir.exists() and list(log_dir.glob("run_*.jsonl"))

    with out.open() as fh:
        reader = csv.reader(fh)
        header = next(reader)
        rows: List[List[str]] = list(reader)

    assert header == CSV_COLUMNS
    assert rows, "expected at least one record"
    assert len(rows) == len(records)

    valid_types = {t.value for t in IncentiveType}
    for row in rows:
        assert len(row) == len(CSV_COLUMNS)
        assert row[CSV_COLUMNS.index("incentive_type")] in valid_types
        assert row[CSV_COLUMNS.index("program_name")].strip()
        assert row[CSV_COLUMNS.index("program_links")].startswith("http")
        assert row[CSV_COLUMNS.index("review_needed")] in {"Yes", "No"}


def test_pipeline_skips_when_fetch_empty(tmp_path: Path):
    out = tmp_path / "incentives.csv"
    review = tmp_path / "review_queue.csv"
    log_dir = tmp_path / "logs"

    def empty_fetcher(source: Source) -> FetchResult:
        return FetchResult(text="", content_type="empty", final_url=source.url)

    records = run_pipeline(
        settings=Settings(),
        output_path=out,
        review_path=review,
        log_dir=log_dir,
        fetcher=empty_fetcher,
        llm=_StubLLM(),
    )

    assert records == []
    # CSV header still written even when zero records.
    with out.open() as fh:
        assert next(csv.reader(fh)) == CSV_COLUMNS
