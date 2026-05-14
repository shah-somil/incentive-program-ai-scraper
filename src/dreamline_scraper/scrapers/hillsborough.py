"""Hillsborough County affordable-housing programs scraper."""

from __future__ import annotations

import logging
from typing import Iterable

from ..extractors.html import make_soup, visible_text
from ..schema import RawIncentive
from .base import BaseScraper
from ._curated import local_baseline

LOGGER = logging.getLogger(__name__)

_URL = "https://hcfl.gov/services/housing"


class HillsboroughScraper(BaseScraper):
    key = "hillsborough"
    name = "Hillsborough County Affordable Housing"

    def scrape(self) -> Iterable[RawIncentive]:
        from ._curated_expanded import local_extras

        baseline = [
            r for r in local_baseline()
            if "Hillsborough" in (r.county or "") or "Hillsborough" in r.program_name
        ]
        baseline.extend(
            r for r in local_extras()
            if (r.county or "") == "Hillsborough" or "Hillsborough" in r.program_name
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
            "https://hcfl.gov/services/housing/own-a-home/home-repairs",
            "https://hcfl.gov/services/housing/buy-a-home/down-payment-assistance",
            "https://hcfl.gov/services/housing/disaster-recovery",
        ]
        out: list[RawIncentive] = []
        for url in urls:
            try:
                resp = self.ctx.session.get(url)
            except Exception as exc:  # pragma: no cover - network
                LOGGER.warning("Hillsborough fetch failed %s: %s", url, exc)
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
                    source_name="Hillsborough County Affordable Housing",
                    content_type="html_text",
                )
            )
        return out
