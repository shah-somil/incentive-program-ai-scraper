"""Run quality-gate assertions over the produced CSV.

Run this after ``dreamline-scraper run``::

    python scripts/quality_gate.py output/Extracted_Tampa_Incentives/extracted_tampa_incentives.csv

The script exits non-zero on any quality-gate failure so it can be wired into
CI later.
"""

from __future__ import annotations

import csv
import sys
from collections import Counter
from pathlib import Path
from typing import List

# Ensure the source layout is importable when run from the repo root.
_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from dreamline_scraper.schema import CSV_COLUMNS, IncentiveType  # noqa: E402


def _fail(label: str, message: str, errors: List[str]) -> None:
    print(f"  FAIL  {label}: {message}")
    errors.append(f"{label}: {message}")


def main(path_str: str) -> int:
    path = Path(path_str)
    if not path.exists():
        print(f"missing CSV: {path}")
        return 2

    errors: List[str] = []
    valid_types = {t.value for t in IncentiveType}

    with path.open() as fh:
        reader = csv.reader(fh)
        rows = list(reader)

    if not rows:
        _fail("nonempty", "CSV is empty", errors)
        return 1

    header = rows[0]
    body = rows[1:]
    print(f"Quality gates for {path} ({len(body)} records)")

    if header != CSV_COLUMNS:
        _fail("columns", f"header mismatch: {header}", errors)
    else:
        print("  PASS  columns: header in required order")

    bad_types = [r[3] for r in body if r[3] not in valid_types]
    if bad_types:
        _fail("incentive_type", f"unrecognised values: {set(bad_types)}", errors)
    else:
        print("  PASS  incentive_type values are in allowed vocabulary")

    review_idx = CSV_COLUMNS.index("review_needed")
    bad_review = [r[review_idx] for r in body if r[review_idx] not in {"Yes", "No"}]
    if bad_review:
        _fail("review_needed", f"unrecognised values: {set(bad_review)}", errors)
    else:
        print("  PASS  review_needed values are Yes/No")

    link_idx = CSV_COLUMNS.index("program_links")
    missing_links = [r[0] for r in body if not r[link_idx].startswith("http")]
    if missing_links:
        _fail("program_links", f"non-URL values for: {missing_links[:5]}", errors)
    else:
        print("  PASS  program_links populated for every row")

    name_idx = CSV_COLUMNS.index("program_name")
    blank_names = [i for i, r in enumerate(body) if not r[name_idx].strip()]
    if blank_names:
        _fail("program_name", f"blank names at rows {blank_names[:5]}", errors)
    else:
        print("  PASS  program_name populated for every row")

    updated_idx = CSV_COLUMNS.index("updated_at")
    bad_dates = [r[updated_idx] for r in body
                 if not (len(r[updated_idx]) == 10 and r[updated_idx][4] == "-")]
    if bad_dates:
        _fail("updated_at", f"non-ISO dates: {set(bad_dates)}", errors)
    else:
        print("  PASS  updated_at uses ISO format")

    if len(body) < 60:
        _fail("coverage", f"only {len(body)} records (target >=60)", errors)
    else:
        print(f"  PASS  coverage: {len(body)} records >= 60 target")

    type_counts = Counter(r[3] for r in body)
    print("  Record distribution by incentive_type:")
    for k in sorted(valid_types):
        print(f"    {type_counts.get(k, 0):4d}  {k}")

    flagged = sum(1 for r in body if r[review_idx] == "Yes")
    pct = (flagged / len(body)) * 100 if body else 0
    print(f"  Review queue: {flagged}/{len(body)} ({pct:.1f}%)")

    if errors:
        print(f"\n{len(errors)} quality gate failure(s):")
        for e in errors:
            print(f"- {e}")
        return 1
    print("\nAll quality gates passed.")
    return 0


if __name__ == "__main__":
    target = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "output/Extracted_Tampa_Incentives/extracted_tampa_incentives.csv"
    )
    sys.exit(main(target))
