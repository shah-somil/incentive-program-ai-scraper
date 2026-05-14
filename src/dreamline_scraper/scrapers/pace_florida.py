"""PACE financing administrators active in Florida.

Attempts to LLM-extract from the public PACE administrator pages, falling
back to the curated catalog (suppressed by ``--disable-curated``).
"""

from __future__ import annotations

import logging
from typing import Iterable, List

from ..extractors.html import make_soup, visible_text
from ..schema import RawIncentive
from .base import BaseScraper
from ._curated import local_baseline

LOGGER = logging.getLogger(__name__)


_LIVE_URLS = [
    "https://www.floridapace.gov/",
    "https://renewfinancial.com/",
    "https://ygrene.com/",
    "https://www.fredelocal.com/",
]


class PACEFloridaScraper(BaseScraper):
    key = "pace_florida"
    name = "PACE Financing (Florida)"

    def scrape(self) -> Iterable[RawIncentive]:
        live = self._scrape_live()

        curated: List[RawIncentive] = [
            r for r in local_baseline()
            if "PACE" in r.program_name
            or "Ygrene" in r.program_name
            or "FRED" in r.program_name
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
                LOGGER.warning("PACE fetch failed %s: %s", url, exc)
                continue
            if not resp.ok:
                LOGGER.info("PACE %s HTTP %s", url, resp.status_code)
                continue
            text = visible_text(make_soup(resp.text))[:12000]
            out.extend(
                self.ctx.llm.parse(
                    content=text,
                    source_url=url,
                    source_name="PACE administrator page",
                    content_type="html_text",
                )
            )
        return out
