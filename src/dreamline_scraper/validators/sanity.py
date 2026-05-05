"""Amount sanity + URL liveness checks."""

from __future__ import annotations

import logging
import re
from typing import List, Optional

from ..schema import IncentiveRecord

LOGGER = logging.getLogger(__name__)


_AMOUNT_RE = re.compile(r"\$?\s*([0-9][0-9,]*\.?[0-9]*)")


def sanitize_amount(text: Optional[str]) -> Optional[str]:
    if not text:
        return None
    cleaned = " ".join(text.split())
    return cleaned[:200] if cleaned else None


def check_link(url: str) -> bool:
    """Return True if URL is reachable. Network failures => True (don't flag).

    The pipeline runs offline-friendly tests; a hard failure here would force
    every record to be flagged.  We only return False when we can affirmatively
    say the URL is broken (HTTP 4xx/5xx).
    """

    if not url:
        return False
    try:
        from ..extractors.http import get_session
        session = get_session()
        return session.head_ok(url)
    except Exception as exc:  # pragma: no cover - defensive
        LOGGER.debug("link check error for %s: %s", url, exc)
        return True


def verify_links(records: List[IncentiveRecord], *, max_checks: int = 0) -> List[IncentiveRecord]:
    """Optionally HEAD-check ``program_links`` and flag broken URLs for review.

    Disabled by default (``max_checks=0``) so offline runs do not generate
    false positives.  Pass ``max_checks=-1`` to check every record.
    """

    if max_checks == 0:
        return records
    out: List[IncentiveRecord] = []
    checked = 0
    for r in records:
        if checked == max_checks and max_checks > 0:
            out.append(r)
            continue
        if not r.program_links:
            out.append(r.model_copy(update={"review_needed": "Yes"}))
            continue
        if not check_link(r.program_links):
            LOGGER.info("broken link for %s -> %s", r.program_name, r.program_links)
            out.append(r.model_copy(update={"review_needed": "Yes"}))
        else:
            out.append(r)
        checked += 1
    return out
