"""CSV writer enforcing the exact required column order."""

from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import Iterable, List

from ..schema import CSV_COLUMNS, CSV_SOURCE_COLUMN, IncentiveRecord

LOGGER = logging.getLogger(__name__)


def write_records(
    path: Path,
    records: Iterable[IncentiveRecord],
    *,
    include_source: bool = False,
) -> int:
    """Write ``records`` to ``path`` using ``CSV_COLUMNS`` order. Returns count.

    When ``include_source=True``, an extra ``extraction_source`` column is
    appended.  This is opt-in so the deliverable CSV keeps the exact required
    12-column schema, while the review queue / debug runs can carry provenance.
    """

    path.parent.mkdir(parents=True, exist_ok=True)
    rows: List[IncentiveRecord] = list(records)
    header = list(CSV_COLUMNS)
    if include_source:
        header.append(CSV_SOURCE_COLUMN)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(header)
        for record in rows:
            writer.writerow(record.as_csv_row(include_source=include_source))
    LOGGER.info("wrote %d records to %s", len(rows), path)
    return len(rows)


def write_review_queue(path: Path, records: Iterable[IncentiveRecord]) -> int:
    """Review queue always carries ``extraction_source`` for debugging."""

    flagged = [r for r in records if r.review_needed == "Yes"]
    return write_records(path, flagged, include_source=True)
