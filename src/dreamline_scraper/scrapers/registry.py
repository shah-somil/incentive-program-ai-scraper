"""Lookup table of scraper classes keyed by source identifier."""

from __future__ import annotations

from typing import Dict, Iterable, List, Optional, Type

from .base import BaseScraper, ScraperContext


def _import_scrapers() -> Dict[str, Type[BaseScraper]]:
    # Lazy import so that test fixtures can run without optional deps.
    from . import (  # noqa: F401
        dsire_florida,
        rewiring_america,
        teco,
        duke_fl,
        msfh,
        fhfc,
        hillsborough,
        tampa,
        irs_25c_25d,
        fema_mitigation,
        pace_florida,
        florida_statutes,
        federal_extras,
        tampa_bay_msa,
    )

    return {
        dsire_florida.DSIREFloridaScraper.key: dsire_florida.DSIREFloridaScraper,
        rewiring_america.RewiringAmericaScraper.key: rewiring_america.RewiringAmericaScraper,
        teco.TECOScraper.key: teco.TECOScraper,
        duke_fl.DukeFloridaScraper.key: duke_fl.DukeFloridaScraper,
        msfh.MySafeFloridaHomeScraper.key: msfh.MySafeFloridaHomeScraper,
        fhfc.FloridaHousingScraper.key: fhfc.FloridaHousingScraper,
        hillsborough.HillsboroughScraper.key: hillsborough.HillsboroughScraper,
        tampa.CityOfTampaScraper.key: tampa.CityOfTampaScraper,
        irs_25c_25d.IRSScraper.key: irs_25c_25d.IRSScraper,
        fema_mitigation.FEMAMitigationScraper.key: fema_mitigation.FEMAMitigationScraper,
        pace_florida.PACEFloridaScraper.key: pace_florida.PACEFloridaScraper,
        florida_statutes.FloridaStatutesScraper.key: florida_statutes.FloridaStatutesScraper,
        federal_extras.FederalExtrasScraper.key: federal_extras.FederalExtrasScraper,
        tampa_bay_msa.TampaBayMSAScraper.key: tampa_bay_msa.TampaBayMSAScraper,
    }


# Lazy-evaluated; populated on first call to :func:`build_scrapers`.
REGISTRY: Dict[str, Type[BaseScraper]] = {}


def build_scrapers(
    keys: Optional[Iterable[str]] = None,
    *,
    ctx: Optional[ScraperContext] = None,
) -> List[BaseScraper]:
    """Instantiate scrapers.  Pass ``keys=None`` for everything in the registry."""

    global REGISTRY
    if not REGISTRY:
        REGISTRY = _import_scrapers()
    selected = list(keys) if keys else list(REGISTRY.keys())
    ctx = ctx or ScraperContext.default()
    out: List[BaseScraper] = []
    for k in selected:
        cls = REGISTRY.get(k)
        if cls is None:
            continue
        out.append(cls(ctx=ctx))
    return out
