"""Florida Housing Finance Corporation scraper.

The Florida Housing site is JS-heavy.  We use Playwright if available, then
hand the rendered HTML to the LLM parser.  When neither Playwright nor the
LLM are available, we fall back to the curated set of Florida Housing
programs (Hometown Heroes, FL Assist, HFA Preferred, SHIP).
"""

from __future__ import annotations

import logging
from typing import Iterable

from ..extractors.html import make_soup, visible_text
from ..schema import RawIncentive
from .base import BaseScraper
from ._curated import state_baseline

LOGGER = logging.getLogger(__name__)

_URL = "https://www.floridahousing.org/programs"


class FloridaHousingScraper(BaseScraper):
    key = "fhfc"
    name = "Florida Housing Finance Corp"

    def scrape(self) -> Iterable[RawIncentive]:
        from ._curated_expanded import state_extras

        baseline = [
            r for r in state_baseline()
            if "Florida Housing Finance Corporation" in (r.program_administrator or "")
        ]
        baseline.extend(
            r for r in state_extras()
            if "Florida Housing" in (r.program_administrator or "")
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
        html = self._fetch_html()
        if not html:
            return []
        text = visible_text(make_soup(html))[:14000]
        if len(text.strip()) < 200:
            return []
        return list(
            self.ctx.llm.parse(
                content=text,
                source_url=_URL,
                source_name="Florida Housing Finance Corp",
                content_type="html_text",
            )
        )

    def _fetch_html(self) -> str:
        try:
            from ..extractors.playwright_runner import render_page
            html = render_page(_URL, wait_selector="main")
            if html:
                return html
        except Exception as exc:  # pragma: no cover - playwright optional
            LOGGER.info("Playwright unavailable for FHFC: %s", exc)
        try:
            resp = self.ctx.session.get(_URL)
            if resp.ok:
                return resp.text
        except Exception as exc:  # pragma: no cover - network
            LOGGER.warning("FHFC fetch failed: %s", exc)
        return ""
