"""Completeness checks that escalate ``review_needed`` to ``"Yes"``."""

from __future__ import annotations

from typing import List

from ..schema import IncentiveRecord


_REQUIRED_NON_EMPTY = (
    "program_name",
    "state",
    "city",
    "property_type",
    "description",
    "incentive_amount",
    "program_links",
)


def enforce_review_flags(records: List[IncentiveRecord]) -> List[IncentiveRecord]:
    """Mutate-and-return records so that any incomplete row is flagged."""

    out: List[IncentiveRecord] = []
    for r in records:
        flagged = r
        reasons: List[str] = []
        for field in _REQUIRED_NON_EMPTY:
            value = getattr(r, field, "")
            if not value or not str(value).strip():
                reasons.append(f"missing {field}")
        if reasons and flagged.review_needed != "Yes":
            flagged = flagged.model_copy(update={"review_needed": "Yes"})
        out.append(flagged)
    return out
