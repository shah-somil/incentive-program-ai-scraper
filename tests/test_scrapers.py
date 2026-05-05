"""Per-scraper smoke tests against curated fallbacks (no network)."""

from __future__ import annotations

import pytest

from dreamline_scraper.scrapers import build_scrapers


SCRAPER_MIN_COUNT = {
    "dsire_florida": 5,
    "rewiring_america": 5,
    "teco": 4,  # 5 curated entries; fallback always provided
    "duke_fl": 3,
    "msfh": 1,
    "fhfc": 4,
    "hillsborough": 4,
    "tampa": 2,
    "irs_25c_25d": 2,
    "fema_mitigation": 2,
    "pace_florida": 3,
    "florida_statutes": 5,
    "federal_extras": 8,
    "tampa_bay_msa": 2,
}


@pytest.mark.parametrize("key,minimum", list(SCRAPER_MIN_COUNT.items()))
def test_curated_fallbacks_yield_records(key: str, minimum: int, monkeypatch):
    # Disable any live HTTP / Playwright / LLM paths so all scrapers fall
    # through to their curated baselines.
    from dreamline_scraper.scrapers.dsire_florida import DSIREFloridaScraper
    monkeypatch.setattr(DSIREFloridaScraper, "_scrape_live", lambda self: iter([]))

    from dreamline_scraper.scrapers.teco import TECOScraper
    monkeypatch.setattr(TECOScraper, "_scrape_live", lambda self: iter([]))

    from dreamline_scraper.parsers.llm_parser import LLMParser
    monkeypatch.setattr(LLMParser, "enabled", property(lambda self: False))

    scraper = build_scrapers([key])[0]
    records = scraper.run()
    assert len(records) >= minimum, (
        f"{key} expected >={minimum} records, got {len(records)}"
    )
    for r in records:
        assert r.program_name.strip()
        assert r.source_url.startswith("http")
