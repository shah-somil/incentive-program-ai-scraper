"""Catch-all source for federal programs beyond the IRS / IRA / FEMA scrapers.

Covers DOE Weatherization, LIHEAP, USDA 504, HUD 203(k), VA EEM, EV credits,
and federal commercial ITC.  These records are sourced directly from the
agency websites cited in :mod:`._curated_expanded`.
"""

from __future__ import annotations

from typing import Iterable

from ..schema import RawIncentive
from .base import BaseScraper


_FEMA_PREFIX = "FEMA"
_IRS_KEYWORDS = ("Section 25C", "Section 25D")


class FederalExtrasScraper(BaseScraper):
    key = "federal_extras"
    name = "Federal extras (DOE WAP, LIHEAP, USDA 504, HUD 203k, VA EEM, EV credits)"

    def scrape(self) -> Iterable[RawIncentive]:
        from ._curated_expanded import federal_extras

        out = []
        for r in federal_extras():
            if r.program_name.startswith(_FEMA_PREFIX):
                continue  # handled by FEMAMitigationScraper
            out.append(r)
        return out
