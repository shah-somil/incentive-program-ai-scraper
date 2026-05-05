"""Duke Energy Florida residential rebates scraper."""

from __future__ import annotations

import logging
from typing import Iterable

from ..schema import RawIncentive
from .base import BaseScraper
from ._curated import utility_baseline

LOGGER = logging.getLogger(__name__)


class DukeFloridaScraper(BaseScraper):
    key = "duke_fl"
    name = "Duke Energy Florida Rebates"

    def scrape(self) -> Iterable[RawIncentive]:
        from ._curated_expanded import utility_extras

        # Duke Energy's product pages are heavily JS-rendered and gate their
        # rebate detail behind an address lookup, so we ship the canonical
        # rebate set from the public Smart $aver brochure as the curated
        # baseline.  The LLM parser can still upgrade these later.
        out: list[RawIncentive] = [
            r for r in utility_baseline()
            if "Duke Energy Florida" in (r.program_administrator or "")
        ]
        out.extend(
            r for r in utility_extras()
            if "Duke Energy Florida" in (r.program_administrator or "")
        )
        return out
