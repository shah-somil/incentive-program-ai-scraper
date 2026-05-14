"""FEMA Hazard Mitigation Grant Program / BRIC scraper.

Attempts a live LLM-assisted extraction of the public FEMA grant program
pages before falling back to the curated catalog.  ``--disable-curated``
suppresses the catalog so the run reflects only what the live extraction
produced.
"""

from __future__ import annotations

import logging
from typing import Iterable, List

from ..extractors.html import make_soup, visible_text
from ..schema import RawIncentive
from .base import BaseScraper
from ._curated import federal_baseline

LOGGER = logging.getLogger(__name__)


_LIVE_URLS = [
    "https://www.fema.gov/grants/mitigation/hazard-mitigation",
    "https://www.fema.gov/grants/mitigation/building-resilient-infrastructure-communities",
]


class FEMAMitigationScraper(BaseScraper):
    key = "fema_mitigation"
    name = "FEMA Hazard Mitigation (HMGP / BRIC)"

    def scrape(self) -> Iterable[RawIncentive]:
        from ._curated_expanded import federal_extras

        live = self._scrape_live()

        curated: List[RawIncentive] = [
            r for r in federal_baseline() if r.program_name.startswith("FEMA")
        ]
        curated.extend(
            r for r in federal_extras() if r.program_name.startswith("FEMA")
        )
        curated = self.curated(curated)

        # When live found anything, dedupe curated by name so we don't double-
        # publish identical programs.
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
                LOGGER.warning("FEMA fetch failed %s: %s", url, exc)
                continue
            if not resp.ok:
                LOGGER.info("FEMA %s HTTP %s", url, resp.status_code)
                continue
            text = visible_text(make_soup(resp.text))[:14000]
            out.extend(
                self.ctx.llm.parse(
                    content=text,
                    source_url=url,
                    source_name="FEMA Hazard Mitigation",
                    content_type="html_text",
                )
            )
        return out
