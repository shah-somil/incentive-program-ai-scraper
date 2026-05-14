"""State-level Florida statutory programs.

Pulls sales-tax exemptions, homestead exemptions, net metering, and veteran
exemptions from the Florida Department of Revenue and Hillsborough County
Property Appraiser pages via the LLM parser, with the curated catalog as
fallback (suppressed by ``--disable-curated``).
"""

from __future__ import annotations

import logging
from typing import Iterable, List

from ..extractors.html import make_soup, visible_text
from ..schema import RawIncentive
from .base import BaseScraper

LOGGER = logging.getLogger(__name__)


_LIVE_URLS = [
    "https://floridarevenue.com/property/Pages/Taxpayers_Exemptions.aspx",
    "https://floridarevenue.com/taxes/taxesfees/Pages/sales_tax.aspx",
    "https://www.hcpafl.org/Property-Info/Exemptions",
    "https://www.floridadisaster.org/dem/mitigation/",
]


class FloridaStatutesScraper(BaseScraper):
    key = "florida_statutes"
    name = "Florida Statutes (Property Tax / Net Metering)"

    def scrape(self) -> Iterable[RawIncentive]:
        from ._curated_expanded import state_extras

        live = self._scrape_live()

        curated: List[RawIncentive] = [
            r for r in state_extras()
            if "Florida Housing" not in (r.program_administrator or "")
        ]
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
                LOGGER.warning("FL statutes fetch failed %s: %s", url, exc)
                continue
            if not resp.ok:
                LOGGER.info("FL statutes %s HTTP %s", url, resp.status_code)
                continue
            text = visible_text(make_soup(resp.text))[:14000]
            out.extend(
                self.ctx.llm.parse(
                    content=text,
                    source_url=url,
                    source_name="Florida statutory exemption page",
                    content_type="html_text",
                )
            )
        return out
