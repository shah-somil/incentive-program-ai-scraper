"""Common scraper interface."""

from __future__ import annotations

import logging
from collections import Counter
from dataclasses import dataclass
from typing import Iterable, List, Optional

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

    @property
    def disable_curated(self) -> bool:
        return bool(getattr(self.ctx.settings, "disable_curated", False))

    def curated(self, records: Iterable[RawIncentive]) -> List[RawIncentive]:
        """Return curated records unless ``disable_curated`` is set.

        Every scraper should funnel its curated-baseline contribution through
        this helper.  When the operator passes ``--disable-curated`` (or sets
        ``DISABLE_CURATED=1``), the curated layer is suppressed and the
        scraper's output reflects only what the live source / API / LLM
        actually produced.
        """

        if self.disable_curated:
            return []
        return list(records)

    def run(self) -> list[RawIncentive]:
        try:
            results = list(self.scrape())
        except Exception as exc:
            LOGGER.exception("%s failed: %s", self.name or self.key, exc)
            return []
        # Breakdown by extraction_source so the audit log can show how much
        # came from each path (live_html / live_api / llm / curated).
        counts = Counter((r.extraction_source or "unknown") for r in results)
        breakdown = ", ".join(f"{k}={v}" for k, v in sorted(counts.items())) or "empty"
        LOGGER.info(
            "%s produced %d records (%s)",
            self.name or self.key,
            len(results),
            breakdown,
        )
        return results
