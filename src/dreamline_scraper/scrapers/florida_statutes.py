"""Catch-all source for state-level Florida statutory programs.

These are programs codified in Florida law (sales-tax exemptions, homestead
exemptions, net metering, veteran exemptions) that do not live on a single
crawlable page.  Their data is sourced from the Florida Department of
Revenue, Hillsborough County Property Appraiser, and the Florida Statutes.
"""

from __future__ import annotations

from typing import Iterable

from ..schema import RawIncentive
from .base import BaseScraper


class FloridaStatutesScraper(BaseScraper):
    key = "florida_statutes"
    name = "Florida Statutes (Property Tax / Net Metering)"

    def scrape(self) -> Iterable[RawIncentive]:
        from ._curated_expanded import state_extras

        # Pick up state extras not already covered by FHFC scraper
        return [
            r for r in state_extras()
            if "Florida Housing" not in (r.program_administrator or "")
        ]
