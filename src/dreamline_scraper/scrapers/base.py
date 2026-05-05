"""Common scraper interface."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Iterable, Optional

from ..config import Settings, load_settings
from ..extractors.http import PoliteSession, get_session
from ..parsers.llm_parser import LLMParser
from ..schema import RawIncentive

LOGGER = logging.getLogger(__name__)


@dataclass
class ScraperContext:
    settings: Settings
    session: PoliteSession
    llm: LLMParser

    @classmethod
    def default(cls) -> "ScraperContext":
        settings = load_settings()
        session = get_session()
        llm = LLMParser(settings=settings)
        return cls(settings=settings, session=session, llm=llm)


class BaseScraper:
    """Subclasses must override :meth:`scrape` to yield ``RawIncentive`` objects."""

    key: str = ""
    name: str = ""

    def __init__(self, ctx: Optional[ScraperContext] = None):
        self.ctx = ctx or ScraperContext.default()

    # Subclasses override these ---------------------------------------------------

    def scrape(self) -> Iterable[RawIncentive]:  # pragma: no cover - interface
        raise NotImplementedError

    # Helpers --------------------------------------------------------------------

    def run(self) -> list[RawIncentive]:
        try:
            results = list(self.scrape())
        except Exception as exc:
            LOGGER.exception("%s failed: %s", self.name or self.key, exc)
            return []
        LOGGER.info("%s produced %d records", self.name or self.key, len(results))
        return results
