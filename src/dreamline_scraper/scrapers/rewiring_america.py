"""Rewiring America IRA calculator scraper / API client.

If a free API key is available (env ``REWIRING_AMERICA_KEY``) we hit
``https://api.rewiringamerica.org/api/v1/calculator`` for a Tampa ZIP and
flatten the response.  Otherwise we fall back to the federal IRA programs
encoded in :mod:`._curated` (residential clean-energy credit, 25C credit,
HOMES + HEEHRA rebates).
"""

from __future__ import annotations

import logging
from typing import Iterable, Iterator, Optional

from ..config import DEFAULT_ZIP
from ..schema import AmountType, Level, RawIncentive, RawType, today_iso
from .base import BaseScraper

LOGGER = logging.getLogger(__name__)

_API_URL = "https://api.rewiringamerica.org/api/v1/calculator"


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
        if self.ctx.settings.rewiring_america_key:
            live = list(self._fetch_api())
            if live:
                return live
        LOGGER.info("Rewiring America falling back to curated federal baseline")
        return list(self._curated_baseline())

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
