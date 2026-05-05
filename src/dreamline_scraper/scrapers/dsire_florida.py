"""DSIRE Florida scraper.

DSIRE's public listing at https://programs.dsireusa.org/system/program?state=FL
returns a paginated set of program detail links.  We parse each detail page
into a :class:`RawIncentive`.  When the live site is unavailable (CI runs,
rate limits) the scraper falls back to a lightweight curated set of the most
relevant Florida-wide programs documented in the kickoff brief.
"""

from __future__ import annotations

import logging
import re
from typing import Iterable, Iterator, List, Optional
from urllib.parse import urljoin

from ..extractors.html import clean_text, make_soup, visible_text
from ..schema import AmountType, Level, RawIncentive, RawType, today_iso
from .base import BaseScraper

LOGGER = logging.getLogger(__name__)


_LISTING_URL = "https://programs.dsireusa.org/system/program?state=FL"
_BASE_URL = "https://programs.dsireusa.org"


_TYPE_TO_RAW: dict[str, RawType] = {
    "tax credit": RawType.tax_credit,
    "personal tax credit": RawType.tax_credit,
    "corporate tax credit": RawType.tax_credit,
    "tax exemption": RawType.exemption,
    "sales tax incentive": RawType.exemption,
    "property tax incentive": RawType.exemption,
    "rebate program": RawType.rebate,
    "utility rebate program": RawType.rebate,
    "grant program": RawType.grant,
    "loan program": RawType.loan,
    "pace financing": RawType.financing,
    "performance-based incentive": RawType.rebate,
    "industry recruitment/support": RawType.investment,
    "green building incentive": RawType.rebate,
}


def _classify_type(text: str) -> Optional[RawType]:
    norm = text.lower()
    for key, value in _TYPE_TO_RAW.items():
        if key in norm:
            return value
    return None


_DOLLAR_RE = re.compile(r"\$\s*([0-9][0-9,]*(?:\.[0-9]+)?)")
_PCT_RE = re.compile(r"([0-9]+(?:\.[0-9]+)?)\s*%")


def _parse_amount(text: str) -> tuple[Optional[AmountType], Optional[float], Optional[float], Optional[str]]:
    """Best-effort numeric amount parse. Returns (type, value, max, raw_text)."""

    norm = text.strip()
    if not norm:
        return None, None, None, None
    pct = _PCT_RE.search(norm)
    dollar = _DOLLAR_RE.search(norm)
    if pct:
        value = float(pct.group(1))
        amax: Optional[float] = None
        if dollar:
            try:
                amax = float(dollar.group(1).replace(",", ""))
            except ValueError:
                amax = None
        return AmountType.percentage, value, amax, norm
    if dollar:
        try:
            value = float(dollar.group(1).replace(",", ""))
        except ValueError:
            return None, None, None, norm
        if "up to" in norm.lower() or "max" in norm.lower():
            return AmountType.up_to, value, None, norm
        return AmountType.fixed_dollar, value, None, norm
    return None, None, None, norm


class DSIREFloridaScraper(BaseScraper):
    key = "dsire_florida"
    name = "DSIRE Florida"

    def scrape(self) -> Iterable[RawIncentive]:
        live = list(self._scrape_live())
        if live:
            return live
        LOGGER.info("DSIRE live scrape returned 0 records; falling back to curated baseline")
        return list(self._curated_baseline())

    # ------------------------------------------------------------------
    # Live scrape
    # ------------------------------------------------------------------

    def _scrape_live(self) -> Iterator[RawIncentive]:
        try:
            resp = self.ctx.session.get(_LISTING_URL)
        except Exception as exc:  # pragma: no cover - network
            LOGGER.warning("DSIRE listing fetch failed: %s", exc)
            return
        if not resp.ok:
            LOGGER.warning("DSIRE listing HTTP %s", resp.status_code)
            return
        soup = make_soup(resp.text)
        program_urls: List[str] = []
        for a in soup.select("a"):
            href = a.get("href", "")
            if "/detail/" in href or "/system/program/detail/" in href:
                program_urls.append(urljoin(_BASE_URL, href))
        program_urls = list(dict.fromkeys(program_urls))[:60]
        LOGGER.info("DSIRE listing found %d program links", len(program_urls))

        for url in program_urls:
            try:
                detail = self.ctx.session.get(url)
            except Exception as exc:  # pragma: no cover - network
                LOGGER.debug("DSIRE detail fetch failed %s: %s", url, exc)
                continue
            if not detail.ok:
                continue
            record = self._parse_detail(detail.text, url)
            if record is not None:
                yield record

    def _parse_detail(self, html: str, url: str) -> Optional[RawIncentive]:
        soup = make_soup(html)
        h1 = soup.find(["h1", "h2"])
        if not h1:
            return None
        program_name = clean_text(h1.get_text())
        if not program_name:
            return None

        body = visible_text(soup)
        type_match = re.search(
            r"(Tax Credit|Tax Exemption|Sales Tax Incentive|Property Tax Incentive|Rebate Program|"
            r"Loan Program|Grant Program|PACE Financing|Performance-Based Incentive|"
            r"Green Building Incentive|Utility Rebate Program|Industry Recruitment[^\.]+)",
            body,
            re.IGNORECASE,
        )
        raw_type = _classify_type(type_match.group(0)) if type_match else None

        level = Level.state  # DSIRE FL listing -> default state level
        if "federal" in body.lower()[:500]:
            level = Level.federal
        elif "utility" in body.lower()[:500]:
            level = Level.utility

        amount_section = re.search(
            r"(?:Incentive Amount|Amount)\s*[:\-]?\s*([^\n]{0,300})", body
        )
        amt_type, amt_value, amt_max, amt_text = (None, None, None, None)
        if amount_section:
            amt_type, amt_value, amt_max, amt_text = _parse_amount(amount_section.group(1))

        admin_match = re.search(r"(?:Administered by|Program Administrator)\s*[:\-]?\s*([^\n]{0,200})", body)
        admin = clean_text(admin_match.group(1)) if admin_match else None

        return RawIncentive(
            program_name=program_name,
            level=level,
            type=raw_type,
            amount_type=amt_type,
            amount_value=amt_value,
            amount_max=amt_max,
            amount_text=amt_text,
            description=clean_text(body[:600]),
            program_administrator=admin,
            source_url=url,
            application_url=url,
            last_verified_at=today_iso(),
            confidence_score=0.65,
        )

    # ------------------------------------------------------------------
    # Curated fallback
    # ------------------------------------------------------------------

    def _curated_baseline(self) -> Iterable[RawIncentive]:
        from ._curated import state_baseline
        from ._curated_expanded import state_extras

        return list(state_baseline()) + list(state_extras())
