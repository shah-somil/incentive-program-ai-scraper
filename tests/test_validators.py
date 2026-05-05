from __future__ import annotations

from dreamline_scraper.normalizer import to_record
from dreamline_scraper.schema import (
    AmountType,
    Level,
    RawIncentive,
    RawType,
)
from dreamline_scraper.validators.completeness import enforce_review_flags


def _full_raw() -> RawIncentive:
    return RawIncentive(
        program_name="X",
        source_url="https://example.com",
        type=RawType.rebate,
        level=Level.utility,
        amount_type=AmountType.fixed_dollar,
        amount_value=100,
        utility_provider="Test Utility",
        eligibility_notes="Owner-occupied required.",
        requires_homeownership=True,
    )


def test_enforce_flags_keeps_clean_records_clean():
    rec = to_record(_full_raw())
    rec = rec.model_copy(update={"review_needed": "No"})
    out = enforce_review_flags([rec])
    assert out[0].review_needed == "No"


def test_enforce_flags_when_missing_required():
    rec = to_record(_full_raw())
    rec = rec.model_copy(update={"review_needed": "No", "program_links": ""})
    out = enforce_review_flags([rec])
    assert out[0].review_needed == "Yes"
