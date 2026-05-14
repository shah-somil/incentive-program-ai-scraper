"""Duke Energy Florida residential rebates scraper.

Duke's Smart $aver product pages are JavaScript-rendered and gate amounts
behind an address lookup. We do three things:

1. Try a plain HTTP GET on the Smart $aver and related residential rebate
   pages — sometimes the static HTML contains the rebate copy.
2. Send the page text through the LLM parser when available.
3. Fall back to the curated baseline (suppressed by ``--disable-curated``).
"""

from __future__ import annotations

import logging
from typing import Iterable, List

from ..extractors.html import make_soup, visible_text
from ..schema import RawIncentive
from .base import BaseScraper
from ._curated import utility_baseline

LOGGER = logging.getLogger(__name__)


_LIVE_URLS = [
    "https://www.duke-energy.com/home/products/save-energy-and-money",
    "https://www.duke-energy.com/home/products/home-energy-check",
    "https://www.duke-energy.com/home/products/smart-thermostat",
    "https://www.duke-energy.com/home/products/neighborhood-energy-saver",
    "https://www.duke-energy.com/home/products/electric-vehicles/charger-prep-credit",
]


class DukeFloridaScraper(BaseScraper):
    key = "duke_fl"
    name = "Duke Energy Florida Rebates"

    def scrape(self) -> Iterable[RawIncentive]:
        from ._curated_expanded import utility_extras

        live = self._scrape_live()

        curated: List[RawIncentive] = [
            r for r in utility_baseline()
            if "Duke Energy Florida" in (r.program_administrator or "")
        ]
        curated.extend(
            r for r in utility_extras()
            if "Duke Energy Florida" in (r.program_administrator or "")
        )
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
                LOGGER.warning("Duke fetch failed %s: %s", url, exc)
                continue
            if not resp.ok:
                LOGGER.info("Duke %s HTTP %s", url, resp.status_code)
                continue
            text = visible_text(make_soup(resp.text))[:12000]
            if len(text.strip()) < 200:
                continue
            out.extend(
                self.ctx.llm.parse(
                    content=text,
                    source_url=url,
                    source_name="Duke Energy Florida residential program page",
                    content_type="html_text",
                )
            )
        return out
