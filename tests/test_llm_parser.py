"""LLM parser wrapper tests (no OpenAI calls)."""

from __future__ import annotations

from datetime import date

from dreamline_scraper.config import Settings
from dreamline_scraper.parsers.llm_parser import LLMParser
from dreamline_scraper.sources import Source


_SAMPLE_SOURCE = Source(
    name="Test City Rebates",
    url="https://example.com/rebates",
    level="city",
    city="Tampa",
)


def test_disabled_without_api_key():
    parser = LLMParser(settings=Settings())
    assert not parser.enabled
    assert parser.parse(
        content="hello world",
        source=_SAMPLE_SOURCE,
        final_url=_SAMPLE_SOURCE.url,
    ) == []


def test_coerce_records_uses_source_hints_and_drops_invalid():
    parser = LLMParser(settings=Settings(openai_api_key="sk-fake"))
    sample = [
        {
            "program_name": "City of Tampa Roof Grant",
            "type": "grant",
            "amount_type": "up_to",
            "amount_value": 10000,
            "description": "Roof replacement up to $10K.",
            "confidence_score": 0.78,
        },
        {
            # missing program_name -> dropped
            "type": "grant",
            "amount_value": 1000,
            "confidence_score": 0.5,
        },
    ]
    out = list(parser._coerce_records(
        sample,
        source=_SAMPLE_SOURCE,
        final_url="https://example.com/rebates/final",
    ))
    assert len(out) == 1
    rec = out[0]
    assert rec.program_name == "City of Tampa Roof Grant"
    assert rec.source_url == "https://example.com/rebates/final"
    assert rec.level.value == "city"
    assert rec.city == "Tampa"
    assert rec.extraction_source == "llm"
    assert rec.last_verified_at == date.today().isoformat()
