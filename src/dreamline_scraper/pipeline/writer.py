"""CSV writer enforcing the exact required column order."""

from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import Iterable, List

from ..schema import CSV_COLUMNS, IncentiveRecord

LOGGER = logging.getLogger(__name__)


def write_records(path: Path, records: Iterable[IncentiveRecord]) -> int:
    """Write ``records`` to ``path`` using ``CSV_COLUMNS`` order. Returns count."""

    path.parent.mkdir(parents=True, exist_ok=True)
    rows: List[IncentiveRecord] = list(records)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(CSV_COLUMNS)
        for record in rows:
            writer.writerow(record.as_csv_row())
    LOGGER.info("wrote %d records to %s", len(rows), path)
    return len(rows)


def write_review_queue(path: Path, records: Iterable[IncentiveRecord]) -> int:
    flagged = [r for r in records if r.review_needed == "Yes"]
    return write_records(path, flagged)
