"""Deduplicate raw incentives keyed on (program_name, level, administrator)."""

from __future__ import annotations

import logging
from typing import Iterable, List, Tuple

from ..schema import RawIncentive

LOGGER = logging.getLogger(__name__)


def _key(raw: RawIncentive) -> Tuple[str, str, str]:
    return (
        _norm(raw.program_name),
        (raw.level.value if raw.level else ""),
        _norm(raw.program_administrator or ""),
    )


def _norm(value: str) -> str:
    return " ".join(value.lower().split())


def dedupe(records: Iterable[RawIncentive]) -> List[RawIncentive]:
    """Keep the first occurrence per dedupe key.

    Ordering matters: scrapers ordered by trust (e.g. IRS before DSIRE) should
    be dispatched first so authoritative copies win.
    """

    seen: dict[Tuple[str, str, str], RawIncentive] = {}
    out: List[RawIncentive] = []
    for raw in records:
        key = _key(raw)
        if key in seen:
            LOGGER.debug("dedupe drop: %s", raw.program_name)
            continue
        seen[key] = raw
        out.append(raw)
    return out
