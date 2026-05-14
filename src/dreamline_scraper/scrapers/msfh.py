"""My Safe Florida Home scraper."""

from __future__ import annotations

import logging
from typing import Iterable

from ..extractors.html import make_soup, visible_text
from ..schema import RawIncentive
from .base import BaseScraper
from ._curated import state_baseline

LOGGER = logging.getLogger(__name__)

_URL = "https://mysafeflhome.com/"


class MySafeFloridaHomeScraper(BaseScraper):
    key = "msfh"
    name = "My Safe Florida Home"

    def scrape(self) -> Iterable[RawIncentive]:
        baseline = self.curated([
            r for r in state_baseline() if r.program_name.startswith("My Safe Florida Home")
        ])

        live = self._scrape_live()
        if live:
            seen = {r.program_name.lower() for r in live}
            baseline = [r for r in baseline if r.program_name.lower() not in seen]
        return list(live) + baseline

    def _scrape_live(self) -> list[RawIncentive]:
        if not self.ctx.llm.enabled:
            return []
        try:
            resp = self.ctx.session.get(_URL)
        except Exception as exc:  # pragma: no cover - network
            LOGGER.warning("MSFH fetch failed: %s", exc)
            return []
        if not resp.ok:
            return []

        text = visible_text(make_soup(resp.text))[:8000]
        if len(text.strip()) < 200:
            return []
        return list(
            self.ctx.llm.parse(
                content=text,
                source_url=_URL,
                source_name="My Safe Florida Home",
                content_type="html_text",
            )
        )
