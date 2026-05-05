"""PACE financing administrators active in Florida."""

from __future__ import annotations

from typing import Iterable

from ..schema import RawIncentive
from .base import BaseScraper
from ._curated import local_baseline


class PACEFloridaScraper(BaseScraper):
    key = "pace_florida"
    name = "PACE Financing (Florida)"

    def scrape(self) -> Iterable[RawIncentive]:
        return [
            r for r in local_baseline()
            if "PACE" in r.program_name or "Ygrene" in r.program_name or "FRED" in r.program_name
        ]
