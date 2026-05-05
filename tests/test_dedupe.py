from __future__ import annotations

from dreamline_scraper.pipeline.dedupe import dedupe
from dreamline_scraper.schema import Level, RawIncentive, RawType


def _r(name: str, level: Level = Level.federal, admin: str = "IRS") -> RawIncentive:
    return RawIncentive(
        program_name=name, level=level, type=RawType.tax_credit,
        program_administrator=admin, source_url="https://example.com",
    )


def test_dedupe_drops_duplicates():
    a = _r("Residential Clean Energy Credit")
    b = _r("Residential Clean Energy Credit")  # same key
    out = dedupe([a, b])
    assert len(out) == 1


def test_dedupe_keeps_distinct_levels():
    a = _r("SHIP", level=Level.state, admin="FHFC")
    b = _r("SHIP", level=Level.county, admin="Hillsborough")
    out = dedupe([a, b])
    assert len(out) == 2
