from __future__ import annotations

import pytest

from dreamline_scraper.schema import (
    CSV_COLUMNS,
    IncentiveRecord,
    IncentiveType,
    RawIncentive,
    Level,
    RawType,
    AmountType,
)


def test_csv_columns_in_required_order():
    assert CSV_COLUMNS == [
        "program_name", "state", "city", "incentive_type", "property_type",
        "description", "eligibility_criteria", "incentive_amount",
        "valid_until", "updated_at", "review_needed", "program_links",
    ]


def test_incentive_type_values():
    assert {t.value for t in IncentiveType} == {
        "Grants", "Rebates", "Finance Solutions", "Tax Credits", "Investments",
    }


def test_record_yes_no_validation():
    base = dict(
        program_name="X", state="FL", city="Tampa",
        incentive_type=IncentiveType.rebates, property_type="All",
        description="x", eligibility_criteria="x", incentive_amount="$1",
        valid_until="Ongoing", updated_at="2026-05-04", program_links="https://x",
    )
    IncentiveRecord(**base, review_needed="No")
    IncentiveRecord(**base, review_needed="Yes")
    with pytest.raises(Exception):
        IncentiveRecord(**base, review_needed="maybe")


def test_raw_incentive_requires_name_and_source_url():
    with pytest.raises(Exception):
        RawIncentive(program_name="", source_url="https://x")
    rec = RawIncentive(
        program_name="Solar credit",
        source_url="https://x",
        type=RawType.tax_credit,
        level=Level.federal,
        amount_type=AmountType.percentage,
        amount_value=30,
    )
    assert rec.program_name == "Solar credit"
    assert rec.confidence_score is None
