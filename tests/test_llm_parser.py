"""LLM parser wrapper tests.

We don't actually hit the OpenAI API.  The tests verify:

1. Parser is disabled when no API key is configured.
2. Coercion of a sample structured LLM payload into ``RawIncentive`` works.
3. Records with missing program_name are dropped.
"""

from __future__ import annotations

from dreamline_scraper.config import Settings
from dreamline_scraper.parsers.llm_parser import LLMParser


def test_disabled_without_api_key():
    parser = LLMParser(settings=Settings())
    assert not parser.enabled
    assert parser.parse(
        content="hello", source_url="https://x", source_name="x"
    ) == []


def test_coerce_records_round_trip():
    parser = LLMParser(settings=Settings(openai_api_key="sk-fake"))
    sample = [
        {
            "program_name": "City of Tampa Roof Grant",
            "type": "grant",
            "level": "city",
            "amount_type": "up_to",
            "amount_value": 10000,
            "description": "Roof replacement up to $10K for income-qualified owners.",
            "confidence_score": 0.78,
        },
        {
            # missing program_name -> should be dropped
            "type": "grant",
            "amount_value": 1000,
            "confidence_score": 0.5,
        },
        {
            "program_name": "Grant with no amount",
            "confidence_score": 0.4,
        },
    ]
    out = list(parser._coerce_records(sample, source_url="https://example.com/x"))
    assert len(out) == 2
    assert out[0].program_name == "City of Tampa Roof Grant"
    assert out[0].source_url == "https://example.com/x"
    assert out[0].confidence_score == 0.78


def test_coerce_records_today_default():
    from datetime import date

    parser = LLMParser(settings=Settings(openai_api_key="sk-fake"))
    out = list(parser._coerce_records(
        [{"program_name": "X", "confidence_score": 0.9}],
        source_url="https://example.com",
    ))
    assert out[0].last_verified_at == date.today().isoformat()
