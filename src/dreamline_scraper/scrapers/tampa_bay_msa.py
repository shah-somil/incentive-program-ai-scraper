"""Tampa Bay MSA neighboring counties (Pinellas, Pasco, Manatee, Hernando)."""

from __future__ import annotations

import logging
from typing import Iterable, List

from ..extractors.html import make_soup, visible_text
from ..schema import RawIncentive
from .base import BaseScraper

LOGGER = logging.getLogger(__name__)


_HOME_COUNTIES = {"Hillsborough"}

# County / city housing-and-community-development landing pages for the MSA.
# Verified live 2026-05-11 (older 2026-05-04 URLs 404'd).
_LIVE_URLS = [
    "https://pinellas.gov/downpayment",
    "https://pinellas.gov/community-development-notices/",
    "https://www.pascocountyfl.net/176/Community-Services",
    "https://www.mymanatee.org/departments/community_and_veterans_services/housing_assistance",
    "https://www.stpete.org/residents/housing___neighborhoods/index.php",
]


class TampaBayMSAScraper(BaseScraper):
    key = "tampa_bay_msa"
    name = "Tampa Bay MSA (Pinellas / Pasco / Manatee)"

    def scrape(self) -> Iterable[RawIncentive]:
        from ._curated_expanded import local_extras

        live = self._scrape_live()

        curated: List[RawIncentive] = []
        for r in local_extras():
            county = r.county or ""
            if county and county not in _HOME_COUNTIES:
                curated.append(r)
            elif (r.city or "").lower() == "st. petersburg":
                curated.append(r)
        curated = self.curated(curated)

        if live:
            seen = {r.program_name.lower() for r in live}
            curated = [r for r in curated if r.program_name.lower() not in seen]

        return list(live) + curated

    def _scrape_live(self) -> List[RawIncentive]:
        if not self.ctx.llm.enabled:
            return []
        out: List[RawIncentive] = []
        for url in _LIVE_URLS:
            try:
                resp = self.ctx.session.get(url)
            except Exception as exc:  # pragma: no cover - network
                LOGGER.warning("MSA fetch failed %s: %s", url, exc)
                continue
            if not resp.ok:
                LOGGER.info("MSA %s HTTP %s", url, resp.status_code)
                continue
            text = visible_text(make_soup(resp.text))[:12000]
            out.extend(
                self.ctx.llm.parse(
                    content=text,
                    source_url=url,
                    source_name="Tampa Bay MSA county housing page",
                    content_type="html_text",
                )
            )
        return out
