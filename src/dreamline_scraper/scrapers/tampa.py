"""City of Tampa housing & community development scraper."""

from __future__ import annotations

import logging
from typing import Iterable

from ..extractors.html import make_soup, visible_text
from ..schema import RawIncentive
from .base import BaseScraper
from ._curated import local_baseline

LOGGER = logging.getLogger(__name__)

_URL = "https://www.tampa.gov/housing-and-community-development"


class CityOfTampaScraper(BaseScraper):
    key = "tampa"
    name = "City of Tampa Housing & Community Development"

    def scrape(self) -> Iterable[RawIncentive]:
        from ._curated_expanded import local_extras

        baseline = [
            r for r in local_baseline()
            if (r.city or "").lower() == "tampa"
        ]
        baseline.extend(
            r for r in local_extras()
            if (r.city or "").lower() == "tampa"
        )
        if not self.ctx.llm.enabled:
            return baseline
        try:
            resp = self.ctx.session.get(_URL)
        except Exception as exc:  # pragma: no cover - network
            LOGGER.warning("Tampa fetch failed: %s", exc)
            return baseline
        if not resp.ok:
            return baseline
        text = visible_text(make_soup(resp.text))[:12000]
        live = self.ctx.llm.parse(
            content=text,
            source_url=_URL,
            source_name="City of Tampa Housing & Community Development",
            content_type="html_text",
        )
        return list(live) or baseline
