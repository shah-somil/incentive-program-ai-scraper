"""FEMA Hazard Mitigation Grant Program / BRIC scraper."""

from __future__ import annotations

import logging
from typing import Iterable

from ..schema import RawIncentive
from .base import BaseScraper
from ._curated import federal_baseline

LOGGER = logging.getLogger(__name__)


class FEMAMitigationScraper(BaseScraper):
    key = "fema_mitigation"
    name = "FEMA Hazard Mitigation (HMGP / BRIC)"

    def scrape(self) -> Iterable[RawIncentive]:
        from ._curated_expanded import federal_extras

        out = [r for r in federal_baseline() if r.program_name.startswith("FEMA")]
        out.extend(r for r in federal_extras() if r.program_name.startswith("FEMA"))
        return out
