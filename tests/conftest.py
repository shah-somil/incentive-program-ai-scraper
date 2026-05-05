"""Shared pytest fixtures."""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


import pytest  # noqa: E402

from dreamline_scraper.config import Settings  # noqa: E402
from dreamline_scraper.parsers.llm_parser import LLMParser  # noqa: E402
from dreamline_scraper.scrapers.base import ScraperContext  # noqa: E402


class _DummySession:
    """Mimics PoliteSession: callers should patch per-test where needed."""

    def get(self, url, **kwargs):  # pragma: no cover - tests patch this
        raise RuntimeError(f"network access disabled in tests ({url})")

    def post(self, url, **kwargs):  # pragma: no cover
        raise RuntimeError("network access disabled in tests")

    def head_ok(self, url, **kwargs):
        return True


@pytest.fixture
def offline_settings() -> Settings:
    return Settings()


@pytest.fixture
def offline_ctx(offline_settings) -> ScraperContext:
    return ScraperContext(
        settings=offline_settings,
        session=_DummySession(),
        llm=LLMParser(settings=offline_settings),
    )
