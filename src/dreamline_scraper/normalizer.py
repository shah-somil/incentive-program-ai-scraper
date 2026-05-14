"""Convert :class:`RawIncentive` objects into final :class:`IncentiveRecord` rows.

The brief uses a 17-field internal schema (Section 14.3); the actual CSV
deliverable demands a leaner 12-field structure with a controlled vocabulary
for ``incentive_type``.  This module is the single place that translates
between the two.
"""

from __future__ import annotations

import logging
from typing import Iterable, List, Optional

from .schema import (
    AmountType,
    IncentiveRecord,
    IncentiveType,
    Level,
    RawIncentive,
    RawType,
    today_iso,
)

LOGGER = logging.getLogger(__name__)


# Map from RawType -> IncentiveType. Investments is only assigned when the
# scraper explicitly tags a program as ``RawType.investment``.
_TYPE_MAP: dict[RawType, IncentiveType] = {
    RawType.tax_credit: IncentiveType.tax_credits,
    RawType.exemption: IncentiveType.tax_credits,
    RawType.grant: IncentiveType.grants,
    RawType.subsidy: IncentiveType.grants,
    RawType.rebate: IncentiveType.rebates,
    RawType.loan: IncentiveType.finance_solutions,
    RawType.financing: IncentiveType.finance_solutions,
    RawType.investment: IncentiveType.investments,
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _format_amount(raw: RawIncentive) -> str:
    """Render a human-friendly amount string from the structured fields.

    Falls back to ``raw.amount_text`` if structured data is missing.
    """

    if raw.amount_type and raw.amount_value is not None:
        v = raw.amount_value
        if raw.amount_type == AmountType.percentage:
            base = f"{_fmt_num(v)}%"
            if raw.amount_max:
                base += f" (up to ${_fmt_num(raw.amount_max)})"
            return base
        if raw.amount_type == AmountType.fixed_dollar:
            return f"${_fmt_num(v)}"
        if raw.amount_type == AmountType.up_to:
            return f"Up to ${_fmt_num(v)}"
        if raw.amount_type == AmountType.per_unit:
            unit = ""
            if raw.eligibility_notes and "per " in raw.eligibility_notes.lower():
                unit = ""
            return f"${_fmt_num(v)} per unit"
        if raw.amount_type == AmountType.tiered:
            return raw.amount_text or "Tiered (see eligibility notes)"
    if raw.amount_text:
        return raw.amount_text.strip()
    return ""


def _fmt_num(v: float) -> str:
    if abs(v - int(v)) < 1e-9:
        return f"{int(v):,}"
    return f"{v:,.2f}"


def _resolve_state_city(raw: RawIncentive) -> tuple[str, str]:
    """Determine ``state`` and ``city`` columns from level + raw geo fields."""

    state = (raw.state or "FL").upper() if raw.state else "FL"
    if raw.level == Level.federal:
        return "USA", "Federal"
    if raw.level == Level.state:
        return state, "Statewide"
    if raw.level == Level.county:
        county = raw.county or "Hillsborough County"
        if not county.endswith("County"):
            county = f"{county} County"
        return state, county
    if raw.level == Level.city:
        return state, raw.city or "Tampa"
    if raw.level == Level.utility:
        provider = raw.utility_provider or "Utility"
        return state, f"{provider} territory"
    # Fall-back: best guess from filled fields
    if raw.city:
        return state, raw.city
    if raw.county:
        return state, raw.county
    return state, "Statewide"


def _property_type(raw: RawIncentive) -> str:
    if raw.eligible_property_types:
        return "; ".join(sorted({p.strip().upper() for p in raw.eligible_property_types if p}))
    return "All"


def _eligibility(raw: RawIncentive) -> str:
    parts: List[str] = []
    if raw.requires_homeownership is True:
        parts.append("Owner-occupied required")
    if raw.income_required is True:
        if raw.income_limit_pct_ami:
            parts.append(f"Income-qualified (≤ {raw.income_limit_pct_ami:g}% AMI)")
        else:
            parts.append("Income-qualified")
    if raw.eligible_project_types:
        parts.append(
            "Eligible projects: " + ", ".join(sorted(set(raw.eligible_project_types)))
        )
    if raw.zip_codes:
        parts.append("ZIP codes: " + ", ".join(sorted(set(raw.zip_codes))))
    if raw.eligibility_notes:
        parts.append(raw.eligibility_notes.strip())
    if raw.program_administrator:
        parts.append(f"Administered by: {raw.program_administrator}")
    return " | ".join([p for p in parts if p])


def _description(raw: RawIncentive) -> str:
    if raw.description:
        return _truncate(raw.description, 600)
    if raw.eligibility_notes:
        return _truncate(raw.eligibility_notes, 600)
    return raw.program_name


def _truncate(text: str, n: int) -> str:
    text = " ".join(text.split())
    return text if len(text) <= n else text[: n - 1].rstrip() + "…"


def _valid_until(raw: RawIncentive) -> str:
    if raw.expires_at:
        return raw.expires_at.strip()
    return "Unknown"


def _is_evergreen(value: str) -> bool:
    return value.strip().lower() in {"ongoing", "permanent", "indefinite", "evergreen"}


def _resolve_incentive_type(raw: RawIncentive) -> Optional[IncentiveType]:
    if raw.type and raw.type in _TYPE_MAP:
        return _TYPE_MAP[raw.type]
    # Fallback heuristic on category keywords
    text = " ".join([raw.description or "", raw.eligibility_notes or "",
                     raw.amount_text or ""]).lower()
    if any(k in text for k in ("tax credit", "tax exemption", "tax-free")):
        return IncentiveType.tax_credits
    if "rebate" in text:
        return IncentiveType.rebates
    if any(k in text for k in ("loan", "financing", "pace")):
        return IncentiveType.finance_solutions
    if "grant" in text:
        return IncentiveType.grants
    return None


def _program_link(raw: RawIncentive) -> str:
    return (raw.application_url or raw.source_url or "").strip()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def to_record(raw: RawIncentive) -> IncentiveRecord:
    """Lossy-flatten a :class:`RawIncentive` to a final :class:`IncentiveRecord`.

    Marks ``review_needed = "Yes"`` whenever a required CSV column cannot be
    populated reliably.
    """

    review_reasons: List[str] = []

    inc_type = _resolve_incentive_type(raw)
    if inc_type is None:
        inc_type = IncentiveType.grants
        review_reasons.append("incentive_type unresolved")

    state, city = _resolve_state_city(raw)
    property_type = _property_type(raw)
    description = _description(raw)
    eligibility = _eligibility(raw) or "See program page"
    if eligibility == "See program page":
        review_reasons.append("eligibility unspecified")
    amount = _format_amount(raw)
    if not amount:
        amount = "See program page"
        review_reasons.append("amount unspecified")
    valid_until = _valid_until(raw)
    if _is_evergreen(valid_until):
        valid_until = "Ongoing"
    elif valid_until == "Unknown":
        review_reasons.append("expiry unknown")
    link = _program_link(raw)
    if not link:
        review_reasons.append("missing link")
    if raw.confidence_score is not None and raw.confidence_score < 0.7:
        review_reasons.append(f"low confidence ({raw.confidence_score:.2f})")

    review_needed = "Yes" if review_reasons else "No"
    if review_reasons:
        eligibility = (
            f"{eligibility} [needs review: {'; '.join(review_reasons)}]"
        ) if eligibility else f"[needs review: {'; '.join(review_reasons)}]"

    return IncentiveRecord(
        program_name=raw.program_name,
        state=state,
        city=city,
        incentive_type=inc_type,
        property_type=property_type,
        description=description,
        eligibility_criteria=eligibility,
        incentive_amount=amount,
        valid_until=valid_until,
        updated_at=raw.last_verified_at or today_iso(),
        review_needed=review_needed,
        program_links=link,
        extraction_source=raw.extraction_source or "unknown",
    )


def to_records(raws: Iterable[RawIncentive]) -> List[IncentiveRecord]:
    out: List[IncentiveRecord] = []
    for raw in raws:
        try:
            out.append(to_record(raw))
        except Exception as exc:  # pragma: no cover - defensive
            LOGGER.warning("normalize failed for %s: %s", raw.program_name, exc)
    return out
