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
        baseline = self.curated(baseline)

        live = self._scrape_live()
        if live:
            seen = {r.program_name.lower() for r in live}
            baseline = [r for r in baseline if r.program_name.lower() not in seen]
        return list(live) + baseline

    def _scrape_live(self) -> list[RawIncentive]:
        if not self.ctx.llm.enabled:
            return []
        urls = [
            _URL,
            "https://www.tampa.gov/housing-and-community-development/programs/buying-a-home",
            "https://www.tampa.gov/housing-and-community-development/programs/owner-occupied-rehabilitation",
        ]
        out: list[RawIncentive] = []
        for url in urls:
            try:
                resp = self.ctx.session.get(url)
            except Exception as exc:  # pragma: no cover - network
                LOGGER.warning("Tampa fetch failed %s: %s", url, exc)
                continue
            if not resp.ok:
                continue
            text = visible_text(make_soup(resp.text))[:12000]
            if len(text.strip()) < 200:
                continue
            out.extend(
                self.ctx.llm.parse(
                    content=text,
                    source_url=url,
                    source_name="City of Tampa Housing & Community Development",
                    content_type="html_text",
                )
            )
        return out
