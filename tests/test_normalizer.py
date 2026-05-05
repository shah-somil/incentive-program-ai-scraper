from __future__ import annotations

from dreamline_scraper.normalizer import to_record, to_records
from dreamline_scraper.schema import (
    AmountType,
    IncentiveType,
    Level,
    RawIncentive,
    RawType,
)


def _raw(**overrides) -> RawIncentive:
    base = dict(
        program_name="Test program",
        source_url="https://example.com",
        type=RawType.rebate,
        level=Level.utility,
        amount_type=AmountType.fixed_dollar,
        amount_value=200,
        utility_provider="Tampa Electric",
        application_url="https://example.com/apply",
        eligibility_notes="Owner-occupied required.",
        requires_homeownership=True,
    )
    base.update(overrides)
    return RawIncentive(**base)


def test_normalize_basic_rebate():
    rec = to_record(_raw())
    assert rec.incentive_type is IncentiveType.rebates
    assert rec.state == "FL"
    assert rec.city.endswith("territory")
    assert rec.incentive_amount == "$200"
    assert rec.property_type == "All"
    assert rec.review_needed in {"Yes", "No"}
    assert rec.program_links.startswith("http")


def test_tax_credit_federal_levels():
    rec = to_record(_raw(type=RawType.tax_credit, level=Level.federal,
                         utility_provider=None,
                         amount_type=AmountType.percentage, amount_value=30))
    assert rec.state == "USA"
    assert rec.city == "Federal"
    assert rec.incentive_type is IncentiveType.tax_credits
    assert rec.incentive_amount == "30%"


def test_county_label_normalises():
    rec = to_record(_raw(type=RawType.grant, level=Level.county,
                         county="Hillsborough", utility_provider=None))
    assert rec.city == "Hillsborough County"


def test_review_needed_when_amount_missing():
    rec = to_record(_raw(amount_type=None, amount_value=None,
                         amount_text=None))
    assert rec.review_needed == "Yes"
    assert "amount unspecified" in rec.eligibility_criteria


def test_to_records_skips_invalid():
    assert to_records([_raw(), _raw(program_name="Other")])
