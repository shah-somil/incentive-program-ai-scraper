"""IRS Energy Tax Credits scraper (Sections 25C / 25D)."""

from __future__ import annotations

import logging
from typing import Iterable

from ..extractors.html import make_soup, visible_text
from ..schema import RawIncentive
from .base import BaseScraper
from ._curated import federal_baseline

LOGGER = logging.getLogger(__name__)

_URLS = [
    "https://www.irs.gov/credits-deductions/residential-clean-energy-credit",
    "https://www.irs.gov/credits-deductions/energy-efficient-home-improvement-credit",
]


class IRSScraper(BaseScraper):
    key = "irs_25c_25d"
    name = "IRS 25C / 25D Energy Tax Credits"

    def scrape(self) -> Iterable[RawIncentive]:
        baseline = [
            r for r in federal_baseline()
            if "(Section 25C)" in r.program_name or "(Section 25D)" in r.program_name
        ]
        if not self.ctx.llm.enabled:
            return baseline

        live: list[RawIncentive] = []
        for url in _URLS:
            try:
                resp = self.ctx.session.get(url)
            except Exception as exc:  # pragma: no cover - network
                LOGGER.warning("IRS fetch failed %s: %s", url, exc)
                continue
            if not resp.ok:
                continue
            text = visible_text(make_soup(resp.text))[:14000]
            live.extend(
                self.ctx.llm.parse(
                    content=text,
                    source_url=url,
                    source_name="IRS Energy Tax Credits",
                    content_type="html_text",
                )
            )
        return live or baseline
