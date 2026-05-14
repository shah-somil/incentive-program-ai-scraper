"""Catch-all source for federal programs beyond IRS / IRA / FEMA scrapers.

Covers DOE Weatherization, LIHEAP, USDA 504, HUD 203(k), VA EEM, EV credits,
and the federal commercial ITC.  Each program has a canonical agency URL —
when the LLM parser is available we send the page content through it; the
curated catalog provides a safety net (suppressed by ``--disable-curated``).
"""

from __future__ import annotations

import logging
from typing import Iterable, List

from ..extractors.html import make_soup, visible_text
from ..schema import RawIncentive
from .base import BaseScraper

LOGGER = logging.getLogger(__name__)


_FEMA_PREFIX = "FEMA"

# Agency pages we attempt to scrape live.  Each URL is the canonical landing
# page for one program.  The LLM parser may extract zero, one, or several
# programs per page.
_LIVE_URLS = [
    "https://www.energy.gov/scep/wap/weatherization-assistance-program",
    "https://www.acf.hhs.gov/ocs/programs/liheap",
    "https://www.rd.usda.gov/programs-services/single-family-housing-programs/single-family-housing-repair-loans-grants/fl",
    "https://www.hud.gov/program_offices/housing/sfh/203k",
    "https://www.benefits.va.gov/HOMELOANS/purchaseco_eem.asp",
    "https://www.irs.gov/credits-deductions/alternative-fuel-vehicle-refueling-property-credit",
    "https://www.irs.gov/credits-deductions/credits-for-new-clean-vehicles-purchased-in-2023-or-after",
    "https://www.irs.gov/credits-deductions/used-clean-vehicle-credit",
    "https://www.irs.gov/credits-deductions/businesses/clean-electricity-investment-credit",
]


class FederalExtrasScraper(BaseScraper):
    key = "federal_extras"
    name = "Federal extras (DOE WAP, LIHEAP, USDA 504, HUD 203k, VA EEM, EV credits)"

    def scrape(self) -> Iterable[RawIncentive]:
        from ._curated_expanded import federal_extras

        live = self._scrape_live()

        curated: List[RawIncentive] = []
        for r in federal_extras():
            if r.program_name.startswith(_FEMA_PREFIX):
                continue  # handled by FEMAMitigationScraper
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
                LOGGER.warning("federal_extras fetch failed %s: %s", url, exc)
                continue
            if not resp.ok:
                LOGGER.info("federal_extras %s HTTP %s", url, resp.status_code)
                continue
            text = visible_text(make_soup(resp.text))[:14000]
            out.extend(
                self.ctx.llm.parse(
                    content=text,
                    source_url=url,
                    source_name="Federal program page",
                    content_type="html_text",
                )
            )
        return out
