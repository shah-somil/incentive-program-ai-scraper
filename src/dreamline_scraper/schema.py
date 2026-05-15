"""Pydantic schemas for the Dreamline incentives pipeline.

Two layers:

* ``RawIncentive`` follows the 17-field schema described in the brief
  ([Dreamline_AI_Brief_Incentives_Process-converted.md], section 3.2 / 14.3).
  Scrapers and the LLM parser both produce this representation.

* ``IncentiveRecord`` is the final 12-column CSV row required by the
  ``Incentive Data Extraction Info`` task.  ``normalizer.to_record`` collapses
  a ``RawIncentive`` (plus original source URL) into an ``IncentiveRecord``.
"""

from __future__ import annotations

from datetime import date
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ---------------------------------------------------------------------------
# Controlled vocabulary -- brief Section 13.1
# ---------------------------------------------------------------------------


class Level(str, Enum):
    federal = "federal"
    state = "state"
    county = "county"
    city = "city"
    utility = "utility"


class RawType(str, Enum):
    tax_credit = "tax_credit"
    grant = "grant"
    rebate = "rebate"
    loan = "loan"
    financing = "financing"
    exemption = "exemption"
    subsidy = "subsidy"
    investment = "investment"


class AmountType(str, Enum):
    fixed_dollar = "fixed_dollar"
    percentage = "percentage"
    per_unit = "per_unit"
    up_to = "up_to"
    tiered = "tiered"


# ---------------------------------------------------------------------------
# Final CSV vocabulary -- "Incentive Data Extraction Info"
# ---------------------------------------------------------------------------


class IncentiveType(str, Enum):
    grants = "Grants"
    rebates = "Rebates"
    finance_solutions = "Finance Solutions"
    tax_credits = "Tax Credits"
    investments = "Investments"


# ---------------------------------------------------------------------------
# Raw extraction model (used by scrapers + LLM parser)
# ---------------------------------------------------------------------------


class RawIncentive(BaseModel):
    """The raw structured extraction from a single source.

    Field set follows brief Section 14.3.  All fields are optional except
    ``program_name`` and ``source_url`` so that incomplete extractions can
    still flow through and be flagged for review.
    """

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    program_name: str
    category: Optional[str] = None
    type: Optional[RawType] = None
    level: Optional[Level] = None
    amount_type: Optional[AmountType] = None
    amount_value: Optional[float] = None
    amount_max: Optional[float] = None
    amount_text: Optional[str] = Field(
        default=None,
        description=(
            "Human-readable amount string preserved verbatim from the source "
            "when structured fields cannot be parsed."
        ),
    )
    eligible_property_types: List[str] = Field(default_factory=list)
    eligible_project_types: List[str] = Field(default_factory=list)
    zip_codes: List[str] = Field(default_factory=list)

    @field_validator("eligible_property_types", "eligible_project_types", "zip_codes", mode="before")
    @classmethod
    def _none_to_empty_list(cls, v):
        # LLMs frequently return null for unset list fields even when the
        # schema requests an array. Coerce to [] so the record validates.
        return [] if v is None else v
    state: Optional[str] = "FL"
    county: Optional[str] = None
    city: Optional[str] = None
    utility_provider: Optional[str] = None
    income_required: Optional[bool] = None
    income_limit_pct_ami: Optional[float] = None
    requires_homeownership: Optional[bool] = None
    eligibility_notes: Optional[str] = None
    description: Optional[str] = None
    application_url: Optional[str] = None
    program_administrator: Optional[str] = None
    source_url: str
    expires_at: Optional[str] = None
    last_verified_at: Optional[str] = None
    confidence_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    active: bool = True
    # Provenance: which extraction path produced this record.
    # Values: "llm" (LLM-parsed page) or "unknown".
    extraction_source: str = "unknown"

    @field_validator("program_name")
    @classmethod
    def _name_not_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("program_name must not be blank")
        return v.strip()


# ---------------------------------------------------------------------------
# Final 12-col CSV row
# ---------------------------------------------------------------------------


CSV_COLUMNS = [
    "program_name",
    "state",
    "city",
    "incentive_type",
    "property_type",
    "description",
    "eligibility_criteria",
    "incentive_amount",
    "valid_until",
    "updated_at",
    "review_needed",
    "program_links",
]


# Optional provenance column appended when ``include_source=True``.
CSV_SOURCE_COLUMN = "extraction_source"


class IncentiveRecord(BaseModel):
    """Final flattened row that maps 1:1 to the required CSV columns."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    program_name: str
    state: str
    city: str
    incentive_type: IncentiveType
    property_type: str
    description: str
    eligibility_criteria: str
    incentive_amount: str
    valid_until: str  # ISO date | "Ongoing" | "Unknown"
    updated_at: str  # ISO date YYYY-MM-DD
    review_needed: str  # "Yes" | "No"
    program_links: str  # URL
    extraction_source: str = "unknown"

    @field_validator("review_needed")
    @classmethod
    def _yes_no(cls, v: str) -> str:
        if v not in {"Yes", "No"}:
            raise ValueError("review_needed must be 'Yes' or 'No'")
        return v

    def as_csv_row(self, include_source: bool = False) -> List[str]:
        row = [
            self.program_name,
            self.state,
            self.city,
            self.incentive_type.value,
            self.property_type,
            self.description,
            self.eligibility_criteria,
            self.incentive_amount,
            self.valid_until,
            self.updated_at,
            self.review_needed,
            self.program_links,
        ]
        if include_source:
            row.append(self.extraction_source or "unknown")
        return row


def today_iso() -> str:
    return date.today().isoformat()
