"""Rewiring America IRA calculator scraper / API client.

Three extraction paths, tried in order:

1. **Live API** when ``REWIRING_AMERICA_KEY`` is set — calls
   ``https://api.rewiringamerica.org/api/v1/calculator`` for a Tampa ZIP
   and flattens the structured response.
2. **Live HTML + LLM parser** — scrape Rewiring America's public IRA
   program pages and ask the LLM to structure them. This works without
   any API key.
3. **Curated baseline** — IRS / IRA / HEEHRA records from
   :mod:`._curated` and :mod:`._curated_expanded` (suppressed by
   ``--disable-curated``).
"""

from __future__ import annotations

import logging
from typing import Iterable, Iterator, List, Optional

from ..config import DEFAULT_ZIP
from ..extractors.html import make_soup, visible_text
from ..schema import AmountType, Level, RawIncentive, RawType, today_iso
from .base import BaseScraper

LOGGER = logging.getLogger(__name__)

_API_URL = "https://api.rewiringamerica.org/api/v1/calculator"

# Public Rewiring America program pages — accessible without an API key.
# We hand each through the LLM parser; expected output is the IRA programs
# described on the page (HEEHRA, HOMES, 25C, 25D, 30D, etc.).
_LIVE_HTML_URLS = [
    "https://www.rewiringamerica.org/app/ira-calculator",
    "https://homes.rewiringamerica.org/federal-incentives",
    "https://www.rewiringamerica.org/policy/inflation-reduction-act",
]


_AUTHORITY_TO_LEVEL = {
    "federal": Level.federal,
    "state": Level.state,
    "city": Level.city,
    "county": Level.county,
    "utility": Level.utility,
    "gas_utility": Level.utility,
    "other": None,
}

_PAYMENT_TO_RAW = {
    "tax_credit": RawType.tax_credit,
    "rebate": RawType.rebate,
    "pos_rebate": RawType.rebate,
    "performance_rebate": RawType.rebate,
    "account_credit": RawType.rebate,
    "assistance_program": RawType.grant,
    "tax_deduction": RawType.tax_credit,
    "loan": RawType.loan,
    "financing": RawType.financing,
}


class RewiringAmericaScraper(BaseScraper):
    key = "rewiring_america"
    name = "Rewiring America (IRA)"

    def scrape(self) -> Iterable[RawIncentive]:
        live: List[RawIncentive] = []
        if self.ctx.settings.rewiring_america_key:
            live.extend(self._fetch_api())
        if not live:
            live.extend(self._fetch_html_via_llm())

        baseline = self.curated(self._curated_baseline())
        if live:
            seen = {r.program_name.lower() for r in live}
            baseline = [r for r in baseline if r.program_name.lower() not in seen]
        else:
            LOGGER.info("Rewiring America falling back to curated federal baseline")
        return list(live) + baseline

    def _fetch_html_via_llm(self) -> List[RawIncentive]:
        if not self.ctx.llm.enabled:
            return []
        out: List[RawIncentive] = []
        for url in _LIVE_HTML_URLS:
            try:
                resp = self.ctx.session.get(url)
            except Exception as exc:  # pragma: no cover - network
                LOGGER.warning("Rewiring America HTML fetch failed %s: %s", url, exc)
                continue
            if not resp.ok:
                LOGGER.info("Rewiring America %s HTTP %s", url, resp.status_code)
                continue
            text = visible_text(make_soup(resp.text))[:14000]
            if len(text.strip()) < 200:
                continue
            out.extend(
                self.ctx.llm.parse(
                    content=text,
                    source_url=url,
                    source_name="Rewiring America IRA program page",
                    content_type="html_text",
                )
            )
        return out

    # ------------------------------------------------------------------
    # Live API
    # ------------------------------------------------------------------

    def _fetch_api(self) -> Iterator[RawIncentive]:
        params = {
            "zip": DEFAULT_ZIP,
            "owner_status": "homeowner",
            "household_income": 75000,
            "household_size": 3,
            "tax_filing": "joint",
        }
        headers = {"Authorization": f"Bearer {self.ctx.settings.rewiring_america_key}"}
        try:
            resp = self.ctx.session.session.get(
                _API_URL,
                params=params,
                headers=headers,
                timeout=self.ctx.settings.http_timeout_s,
            )
        except Exception as exc:  # pragma: no cover - network
            LOGGER.warning("Rewiring America API call failed: %s", exc)
            return
        if not resp.ok:
            LOGGER.warning(
                "Rewiring America API HTTP %s: %s", resp.status_code, resp.text[:200]
            )
            return
        try:
            data = resp.json()
        except ValueError:
            LOGGER.warning("Rewiring America API returned non-JSON")
            return
        for entry in data.get("incentives", []) or []:
            yield from self._coerce(entry)

    def _coerce(self, entry: dict) -> Iterator[RawIncentive]:
        program = entry.get("program") or entry.get("program_title") or entry.get("short_description")
        if not program:
            return
        level = _AUTHORITY_TO_LEVEL.get(entry.get("authority_type", ""), None) or Level.federal
        raw_type = _PAYMENT_TO_RAW.get(entry.get("payment_methods", [""])[0]
                                       if isinstance(entry.get("payment_methods"), list)
                                       else entry.get("payment_method", ""), None)
        amt_type, amt_value, amt_max = (None, None, None)
        amount = entry.get("amount", {})
        if isinstance(amount, dict):
            unit = (amount.get("unit") or "").lower()
            value = amount.get("number")
            if unit == "percent":
                amt_type, amt_value = AmountType.percentage, _to_float(value)
            elif unit in ("dollars", "dollar"):
                amt_type, amt_value = AmountType.fixed_dollar, _to_float(value)
            if amount.get("maximum"):
                amt_max = _to_float(amount.get("maximum"))
                if amt_type is None:
                    amt_type = AmountType.up_to
                    amt_value = amt_max
        yield RawIncentive(
            program_name=str(program),
            type=raw_type,
            level=level,
            amount_type=amt_type,
            amount_value=amt_value,
            amount_max=amt_max,
            amount_text=entry.get("short_description"),
            description=entry.get("short_description") or entry.get("title"),
            eligibility_notes=entry.get("eligible") or entry.get("more_info_url"),
            program_administrator=entry.get("authority_name"),
            application_url=entry.get("more_info_url") or entry.get("url"),
            source_url=entry.get("more_info_url") or "https://www.rewiringamerica.org/",
            last_verified_at=today_iso(),
            confidence_score=0.85,
            extraction_source="live_api",
        )

    def _curated_baseline(self) -> Iterable[RawIncentive]:
        from ._curated import federal_baseline
        from ._curated_expanded import federal_extras

        return list(federal_baseline()) + list(federal_extras())


def _to_float(v) -> Optional[float]:
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None
