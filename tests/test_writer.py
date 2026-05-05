"""CSV writer tests."""

from __future__ import annotations

import csv
from pathlib import Path

from dreamline_scraper.pipeline.writer import write_records, write_review_queue
from dreamline_scraper.schema import CSV_COLUMNS, IncentiveRecord, IncentiveType


def _row(name: str, review: str = "No") -> IncentiveRecord:
    return IncentiveRecord(
        program_name=name, state="FL", city="Tampa",
        incentive_type=IncentiveType.rebates, property_type="All",
        description="d", eligibility_criteria="e", incentive_amount="$1",
        valid_until="Ongoing", updated_at="2026-05-04",
        review_needed=review, program_links="https://example.com",
    )


def test_writer_emits_required_header_and_row(tmp_path: Path):
    out = tmp_path / "incentives.csv"
    n = write_records(out, [_row("A"), _row("B", "Yes")])
    assert n == 2
    with out.open() as fh:
        rows = list(csv.reader(fh))
    assert rows[0] == CSV_COLUMNS
    assert rows[1][0] == "A"
    assert rows[2][CSV_COLUMNS.index("review_needed")] == "Yes"


def test_review_queue_only_writes_yes(tmp_path: Path):
    out = tmp_path / "review.csv"
    n = write_review_queue(out, [_row("A"), _row("B", "Yes")])
    assert n == 1
