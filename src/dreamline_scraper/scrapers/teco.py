"""Tampa Electric (TECO) residential rebates scraper."""

from __future__ import annotations

import logging
import re
from typing import Iterable, Iterator, List

from ..extractors.html import clean_text, make_soup, visible_text
from ..schema import AmountType, Level, RawIncentive, RawType, today_iso
from .base import BaseScraper
from ._curated import utility_baseline

LOGGER = logging.getLogger(__name__)

_REBATES_URL = "https://www.tampaelectric.com/residential/saveenergy/"

_REBATE_SUBPAGES = [
    "https://www.tampaelectric.com/residential/saveenergy/energyplanner/",
    "https://www.tampaelectric.com/residential/saveenergy/energyaudit/",
    "https://www.tampaelectric.com/residential/saveenergy/heatingcooling/",
    "https://www.tampaelectric.com/residential/saveenergy/ceilinginsulation/",
    "https://www.tampaelectric.com/residential/saveenergy/ductwork/",
    "https://www.tampaelectric.com/residential/saveenergy/energystarsmartthermostat/",
    "https://www.tampaelectric.com/residential/saveenergy/neighborhoodweatherization/",
    "https://www.tampaelectric.com/residential/saveenergy/primetimeplus/",
]


class TECOScraper(BaseScraper):
    key = "teco"
    name = "TECO (Tampa Electric) Rebates"

    def scrape(self) -> Iterable[RawIncentive]:
        from ._curated_expanded import utility_extras

        def is_teco(r: RawIncentive) -> bool:
            admin = (r.program_administrator or "").lower()
            return "tampa electric" in admin or "teco" in admin or "peoples gas" in admin

        live = list(self._scrape_live())
        baseline = [r for r in utility_baseline() if is_teco(r)]
        baseline += [r for r in utility_extras() if is_teco(r)]
        seen = {r.program_name.lower() for r in live}
        for r in baseline:
            if r.program_name.lower() not in seen:
                live.append(r)
        return live

    def _scrape_live(self) -> Iterator[RawIncentive]:
        for url in [_REBATES_URL, *_REBATE_SUBPAGES]:
            try:
                resp = self.ctx.session.get(url)
            except Exception as exc:  # pragma: no cover - network
                LOGGER.warning("TECO fetch failed for %s: %s", url, exc)
                continue
            if not resp.ok:
                LOGGER.info("TECO %s HTTP %s", url, resp.status_code)
                continue
            soup = make_soup(resp.text)
            text = visible_text(soup)
            sentences = re.split(r"(?<=[.!?])\s+", text)
            seen: set[str] = set()
            for sentence in sentences:
                if "rebate" not in sentence.lower():
                    continue
                if "$" not in sentence:
                    continue
                cand = clean_text(sentence)[:280]
                name = _extract_name(cand)
                if not name:
                    continue
                if cand.lower() in seen:
                    continue
                seen.add(cand.lower())
                yield RawIncentive(
                    program_name=name,
                    level=Level.utility,
                    type=RawType.rebate,
                    amount_text=cand,
                    eligible_property_types=["sfh", "condo", "townhouse"],
                    requires_homeownership=True,
                    income_required=False,
                    utility_provider="Tampa Electric (TECO)",
                    description=cand,
                    source_url=url,
                    application_url=url,
                    program_administrator="Tampa Electric",
                    expires_at="Ongoing",
                    last_verified_at=today_iso(),
                    confidence_score=0.55,
                )


def _extract_name(text: str) -> str:
    """Best-effort program name from a sentence containing 'rebate'."""

    m = re.search(r"([A-Z][A-Za-z0-9 /\-]{2,60}\brebate\b)", text)
    return m.group(1).strip().rstrip(":") if m else ""
