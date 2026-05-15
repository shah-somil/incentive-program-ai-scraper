"""Declarative list of pages to scrape.

This is the only place the pipeline learns *where* to look.  Each entry is
a single URL plus hints (level, jurisdiction) that the LLM uses to ground
its extraction.  No program data, amounts, or eligibility text lives here.

To make discovery dynamic later, a separate ``discoverer`` module can write
proposed entries to a ``candidates`` queue that a human promotes into this
list.  Keeping ``sources.py`` human-curated protects against the LLM
proposing dead URLs or marketing pages.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class Source:
    name: str
    url: str
    level: str  # federal | state | county | city | utility
    state: str = "FL"
    county: str = ""
    city: str = ""
    utility: str = ""
    # Render mode hint. "auto" tries static first and falls back to a
    # headless browser if the static fetch returns very little text.
    render: str = "auto"  # auto | static | js
    # Optional CSS selector to wait for before reading rendered HTML.
    # Used on SPAs that paint content after JS hydration.
    wait_selector: Optional[str] = None
    # Optional override for Playwright's per-page timeout (ms).
    timeout_ms: int = 45_000

    @property
    def jurisdiction(self) -> str:
        if self.level == "federal":
            return "United States"
        if self.level == "state":
            return self.state or "FL"
        if self.level == "county":
            return f"{self.county}, {self.state}" if self.county else self.state
        if self.level == "city":
            return f"{self.city}, {self.state}" if self.city else self.state
        if self.level == "utility":
            return f"{self.utility} service territory"
        return ""


SOURCES: List[Source] = [
    # --- Federal ---------------------------------------------------------
    Source(
        name="IRS — Home Energy Tax Credits hub",
        url="https://www.irs.gov/credits-deductions/home-energy-tax-credits",
        level="federal",
    ),
    Source(
        name="IRS — Energy Efficient Home Improvement Credit (25C)",
        url="https://www.irs.gov/credits-deductions/energy-efficient-home-improvement-credit",
        level="federal",
    ),
    Source(
        name="IRS — Residential Clean Energy Credit (25D)",
        url="https://www.irs.gov/credits-deductions/residential-clean-energy-credit",
        level="federal",
    ),
    Source(
        name="IRS — Alternative Fuel Vehicle Refueling Property Credit (30C)",
        url="https://www.irs.gov/credits-deductions/alternative-fuel-vehicle-refueling-property-credit",
        level="federal",
    ),
    Source(
        name="IRS — New Clean Vehicle Credit (30D)",
        url="https://www.irs.gov/credits-deductions/credits-for-new-clean-vehicles-purchased-in-2023-or-after",
        level="federal",
    ),
    Source(
        name="IRS — Used Clean Vehicle Credit (25E)",
        url="https://www.irs.gov/credits-deductions/used-clean-vehicle-credit",
        level="federal",
    ),
    Source(
        name="DOE — Weatherization Assistance Program",
        url="https://www.energy.gov/scep/wap/weatherization-assistance-program",
        level="federal",
    ),
    Source(
        name="FEMA — Hazard Mitigation Grant Program",
        url="https://www.fema.gov/grants/mitigation/hazard-mitigation",
        level="federal",
    ),
    Source(
        name="FEMA — Building Resilient Infrastructure & Communities (BRIC)",
        url="https://www.fema.gov/grants/mitigation/building-resilient-infrastructure-communities",
        level="federal",
    ),
    Source(
        name="FEMA — Flood Mitigation Assistance",
        url="https://www.fema.gov/grants/mitigation/floods",
        level="federal",
    ),
    Source(
        name="HUD — 203(k) Rehabilitation Mortgage Insurance",
        url="https://www.hud.gov/program_offices/housing/sfh/203k",
        level="federal",
        render="js",
    ),
    Source(
        # rd.usda.gov is extremely slow to serve over HTTP; the static path
        # routinely exhausts retries. Going straight to a headless browser
        # is faster and more reliable here.
        name="USDA — Single Family Housing Repair Loans & Grants (Section 504)",
        url="https://www.rd.usda.gov/programs-services/single-family-housing-programs/single-family-housing-repair-loans-grants",
        level="federal",
        render="js",
        wait_selector="main",
        timeout_ms=60_000,
    ),
    Source(
        name="VA — Energy Efficient Mortgage",
        url="https://www.va.gov/housing-assistance/home-loans/loan-types/energy-efficient-mortgage/",
        level="federal",
        render="js",
        wait_selector="main",
    ),
    Source(
        name="Rewiring America — Federal Incentives",
        url="https://homes.rewiringamerica.org/federal-incentives",
        level="federal",
        render="js",
        wait_selector="main",
    ),

    # --- State (Florida) -------------------------------------------------
    Source(
        name="DSIRE — Florida programs",
        url="https://programs.dsireusa.org/system/program?state=FL",
        level="state",
        render="js",
        wait_selector="table",
        timeout_ms=60_000,
    ),
    Source(
        name="My Safe Florida Home",
        url="https://mysafeflhome.com/",
        level="state",
    ),
    Source(
        name="Florida Housing Finance Corporation — Programs",
        url="https://www.floridahousing.org/programs",
        level="state",
        render="js",
        wait_selector="main",
    ),
    Source(
        name="Florida Housing Finance Corporation — Homebuyer Overview",
        url="https://www.floridahousing.org/programs/homebuyer-overview-page",
        level="state",
        render="js",
        wait_selector="main",
    ),
    Source(
        name="Florida Dept. of Revenue — Property Tax Exemptions",
        url="https://floridarevenue.com/property/Pages/Taxpayers_Exemptions.aspx",
        level="state",
    ),
    Source(
        name="Florida PACE Funding Agency",
        url="https://www.floridapace.gov/",
        level="state",
    ),

    # --- County / City ---------------------------------------------------
    Source(
        name="Hillsborough County — Residents portal (housing links)",
        url="https://hcfl.gov/residents",
        level="county",
        county="Hillsborough",
        render="js",
        wait_selector="main",
    ),
    Source(
        name="City of Tampa — Housing & Community Development",
        url="https://www.tampa.gov/housing-and-community-development",
        level="city",
        city="Tampa",
        county="Hillsborough",
    ),
    Source(
        name="Pinellas County — Community Development",
        url="https://pinellas.gov/community-development/",
        level="county",
        county="Pinellas",
    ),
    Source(
        name="Pasco County — Government homepage",
        url="https://www.pascocountyfl.gov/",
        level="county",
        county="Pasco",
        render="js",
        wait_selector="main",
    ),
    Source(
        name="Manatee County — Government homepage",
        url="https://www.mymanatee.org/",
        level="county",
        county="Manatee",
        render="js",
        wait_selector="main",
    ),

    # --- Utilities -------------------------------------------------------
    Source(
        name="TECO (Tampa Electric) — Save Energy hub",
        url="https://www.tampaelectric.com/residential/saveenergy/",
        level="utility",
        utility="Tampa Electric (TECO)",
    ),
    Source(
        name="Duke Energy Florida — Home Products",
        url="https://www.duke-energy.com/home/products?jur=FPC",
        level="utility",
        utility="Duke Energy Florida",
        render="js",
        wait_selector="main",
    ),
    Source(
        name="Peoples Gas — Save Energy hub",
        url="https://www.peoplesgas.com/save/",
        level="utility",
        utility="Peoples Gas",
    ),
]
