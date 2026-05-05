"""Tampa Bay MSA neighboring counties (Pinellas, Pasco, Manatee, Hernando).

The brief calls out Tampa Bay MSA expansion (Section 16.1) as Phase 2.  We
include a starter set so the deliverable can be filtered or expanded as the
team prioritises.
"""

from __future__ import annotations

from typing import Iterable

from ..schema import RawIncentive
from .base import BaseScraper


_HOME_COUNTIES = {"Hillsborough"}


class TampaBayMSAScraper(BaseScraper):
    key = "tampa_bay_msa"
    name = "Tampa Bay MSA (Pinellas / Pasco / Manatee)"

    def scrape(self) -> Iterable[RawIncentive]:
        from ._curated_expanded import local_extras

        out = []
        for r in local_extras():
            county = r.county or ""
            if county and county not in _HOME_COUNTIES:
                out.append(r)
            elif (r.city or "").lower() == "st. petersburg":
                out.append(r)
        return out
