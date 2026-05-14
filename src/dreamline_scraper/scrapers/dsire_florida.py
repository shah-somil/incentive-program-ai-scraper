"""DSIRE Florida scraper.

DSIRE's public listing is an Angular SPA, so a plain GET typically returns
zero ``/detail/`` links.  We try several strategies in order:

1. **JSON API** (``/api/v1/programs?state=FL``) — undocumented but stable.
2. **Playwright render** of the SPA listing page when the browser binary
   is installed locally.
3. **Plain GET** of the static HTML as a last-ditch fallback (rarely yields
   anything useful for SPA-rendered pages).

Whatever the discovery path, each program detail URL is then fetched and
parsed into a :class:`RawIncentive`.  When every live path fails the scraper
falls back to the curated state baseline (suppressed by
``--disable-curated``).
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
_API_URL = "https://programs.dsireusa.org/api/v1/programs?state=FL"
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
        baseline = self.curated(list(self._curated_baseline()))
        if live:
            seen = {r.program_name.lower() for r in live}
            baseline = [r for r in baseline if r.program_name.lower() not in seen]
            return list(live) + baseline
        LOGGER.info("DSIRE live scrape returned 0 records; falling back to curated baseline")
        return baseline

    # ------------------------------------------------------------------
    # Live scrape
    # ------------------------------------------------------------------

    def _scrape_live(self) -> Iterator[RawIncentive]:
        program_urls = self._discover_program_urls()
        LOGGER.info("DSIRE discovered %d program links", len(program_urls))
        # Cap detail fetches so a full run completes in reasonable time when
        # we're rendering each page in Playwright.
        for url in program_urls[:30]:
            html = self._fetch_detail_html(url)
            if not html:
                continue
            record = self._parse_detail(html, url)
            if record is not None:
                yield record

    def _fetch_detail_html(self, url: str) -> str:
        """Try Playwright first (DSIRE pages are SPA-rendered); plain GET as fallback."""

        try:
            from ..extractors.playwright_runner import render_page

            html = render_page(
                url,
                wait_selector="h1, h2, .program-name, .program-overview",
                timeout_ms=30000,
            )
            if html and "{{" not in html[:5000]:
                return html
        except Exception as exc:  # pragma: no cover - playwright env
            LOGGER.debug("DSIRE playwright detail render failed %s: %s", url, exc)
        try:
            detail = self.ctx.session.get(url)
            if detail.ok:
                return detail.text
        except Exception as exc:  # pragma: no cover - network
            LOGGER.debug("DSIRE detail fetch failed %s: %s", url, exc)
        return ""

    def _discover_program_urls(self) -> List[str]:
        # Strategy 1 -- JSON API (undocumented but commonly available)
        urls = self._urls_from_api()
        if urls:
            return urls[:80]

        # Strategy 2 -- Playwright render of the SPA
        urls = self._urls_from_playwright()
        if urls:
            return urls[:80]

        # Strategy 3 -- plain GET of the SPA shell (usually empty)
        urls = self._urls_from_static_html()
        return urls[:80]

    def _urls_from_api(self) -> List[str]:
        try:
            resp = self.ctx.session.session.get(
                _API_URL, timeout=self.ctx.settings.http_timeout_s
            )
        except Exception as exc:  # pragma: no cover - network
            LOGGER.debug("DSIRE API fetch failed: %s", exc)
            return []
        if not resp.ok:
            LOGGER.debug("DSIRE API HTTP %s", resp.status_code)
            return []
        try:
            payload = resp.json()
        except ValueError:
            return []
        items = payload.get("data") or payload.get("programs") or payload
        out: List[str] = []
        if isinstance(items, list):
            for entry in items:
                if not isinstance(entry, dict):
                    continue
                pid = entry.get("id") or entry.get("program_id")
                if pid:
                    out.append(f"{_BASE_URL}/detail/{pid}")
        return out

    def _urls_from_playwright(self) -> List[str]:
        try:
            from ..extractors.playwright_runner import render_page
        except Exception:  # pragma: no cover - optional dep
            return []
        try:
            html = render_page(_LISTING_URL, wait_selector="a[href*='/detail/']")
        except Exception as exc:  # pragma: no cover - playwright env
            LOGGER.debug("DSIRE playwright render failed: %s", exc)
            return []
        if not html:
            return []
        return self._extract_detail_links(html)

    def _urls_from_static_html(self) -> List[str]:
        try:
            resp = self.ctx.session.get(_LISTING_URL)
        except Exception as exc:  # pragma: no cover - network
            LOGGER.warning("DSIRE listing fetch failed: %s", exc)
            return []
        if not resp.ok:
            LOGGER.warning("DSIRE listing HTTP %s", resp.status_code)
            return []
        return self._extract_detail_links(resp.text)

    @staticmethod
    def _extract_detail_links(html: str) -> List[str]:
        soup = make_soup(html)
        urls: List[str] = []
        for a in soup.select("a"):
            href = a.get("href", "")
            if "/detail/" in href or "/system/program/detail/" in href:
                urls.append(urljoin(_BASE_URL, href))
        return list(dict.fromkeys(urls))

    def _parse_detail(self, html: str, url: str) -> Optional[RawIncentive]:
        soup = make_soup(html)
        h1 = soup.find(["h1", "h2"])
        if not h1:
            return None
        program_name = clean_text(h1.get_text())
        if not program_name:
            return None
        # DSIRE is an Angular SPA; the static HTML often returns template
        # placeholders like ``{{ program.name }}`` instead of real values.
        # Reject those rather than emit garbage records.
        if "{{" in program_name or "}}" in program_name:
            return None
        if program_name.lower() in {
            "primary navigation",
            "dsire",
            "database of state incentives for renewables & efficiency",
        }:
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
            extraction_source="live_html",
        )

    # ------------------------------------------------------------------
    # Curated fallback
    # ------------------------------------------------------------------

    def _curated_baseline(self) -> Iterable[RawIncentive]:
        from ._curated import state_baseline
        from ._curated_expanded import state_extras

        return list(state_baseline()) + list(state_extras())
