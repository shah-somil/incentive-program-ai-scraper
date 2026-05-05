"""Project-wide configuration.

This file holds non-secret settings such as the source registry, target ZIP
codes, output paths, and rate-limit defaults.  Secrets are loaded from
environment variables / .env via ``load_settings()``.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # pragma: no cover - dotenv is optional at runtime
    pass


PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "output" / "Extracted_Tampa_Incentives"
LOG_DIR = PROJECT_ROOT / "output" / "logs"
CACHE_DIR = PROJECT_ROOT / ".cache"

OUTPUT_CSV = OUTPUT_DIR / "extracted_tampa_incentives.csv"
REVIEW_QUEUE_CSV = LOG_DIR / "review_queue.csv"


# Tampa / Hillsborough County ZIP codes (per brief 16.1 -- ~40 ZIPs).
TAMPA_ZIPS: List[str] = [
    "33602", "33603", "33604", "33605", "33606", "33607", "33609", "33610",
    "33611", "33612", "33613", "33614", "33615", "33616", "33617", "33618",
    "33619", "33620", "33621", "33624", "33625", "33626", "33629", "33634",
    "33635", "33637", "33647",
]

HILLSBOROUGH_OTHER_ZIPS: List[str] = [
    "33510", "33511", "33527", "33534", "33547", "33548", "33549", "33556",
    "33558", "33559", "33563", "33565", "33566", "33567", "33569", "33570",
    "33572", "33573", "33578", "33579", "33584", "33592", "33594", "33596",
    "33598",
]

DEFAULT_ZIP = "33602"  # Downtown Tampa -- used for Rewiring America calculator


# ---------------------------------------------------------------------------
# Source registry
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SourceMeta:
    key: str
    name: str
    priority: str  # "P0" | "P1" | "P2"
    base_url: str
    notes: str = ""


SOURCES: List[SourceMeta] = [
    SourceMeta("dsire_florida", "DSIRE Florida", "P0",
               "https://programs.dsireusa.org/system/program?state=FL",
               "Public listing + program detail pages."),
    SourceMeta("rewiring_america", "Rewiring America (IRA)", "P0",
               "https://api.rewiringamerica.org/api/v1/calculator",
               "Federal IRA programs. Free API key recommended."),
    SourceMeta("teco", "TECO (Tampa Electric) Rebates", "P0",
               "https://www.tampaelectric.com/residential/saveenergy/",
               "Static HTML scraper."),
    SourceMeta("duke_fl", "Duke Energy Florida Rebates", "P1",
               "https://www.duke-energy.com/home/products",
               "Static HTML scraper."),
    SourceMeta("msfh", "My Safe Florida Home", "P1",
               "https://mysafeflhome.com/",
               "Hurricane mitigation grant."),
    SourceMeta("fhfc", "Florida Housing Finance Corp", "P1",
               "https://www.floridahousing.org/programs",
               "SHIP / HOME / DPA programs."),
    SourceMeta("hillsborough", "Hillsborough County Affordable Housing", "P1",
               "https://hcfl.gov/services/housing",
               "SHIP / CDBG / down-payment programs."),
    SourceMeta("tampa", "City of Tampa Housing & Community Dev.", "P2",
               "https://www.tampa.gov/housing-and-community-development",
               "Local rehab programs."),
    SourceMeta("irs_25c_25d", "IRS Energy Efficient Home / Residential Clean Energy", "P1",
               "https://www.irs.gov/credits-deductions/home-energy-tax-credits",
               "Federal 25C + 25D credits."),
    SourceMeta("fema_mitigation", "FEMA Hazard Mitigation (HMGP / BRIC)", "P2",
               "https://www.fema.gov/grants/mitigation",
               "Federal mitigation programs."),
    SourceMeta("pace_florida", "PACE Financing (Ygrene / RenewPACE / FRED)", "P2",
               "https://www.floridapace.gov/",
               "PACE financing for solar / HVAC / roofing."),
    SourceMeta("florida_statutes", "Florida Statutes (Property Tax / Net Metering)", "P1",
               "https://www.hcpafl.org/Property-Info/Exemptions",
               "Statewide statutory exemptions and net metering."),
    SourceMeta("federal_extras", "Federal extras (DOE WAP, USDA 504, HUD 203k, EV credits)", "P1",
               "https://www.energy.gov/scep/wap/weatherization-assistance-program",
               "Federal programs not covered by IRS / IRA / FEMA scrapers."),
    SourceMeta("tampa_bay_msa", "Tampa Bay MSA (Pinellas / Pasco / Manatee)", "P2",
               "https://pinellas.gov/buy-rent-improve-home/",
               "Neighboring-county housing assistance programs."),
]


SOURCE_KEYS = [s.key for s in SOURCES]


# ---------------------------------------------------------------------------
# Runtime settings
# ---------------------------------------------------------------------------


@dataclass
class Settings:
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o-mini"
    rewiring_america_key: Optional[str] = None
    dsire_key: Optional[str] = None
    user_agent: str = (
        "DreamlineAI-Scraper/0.1 (+https://dreamlineai.org/scraper) "
        "research-data-collection"
    )
    request_min_interval_s: float = 1.0
    http_timeout_s: float = 30.0
    enabled_sources: List[str] = field(default_factory=lambda: list(SOURCE_KEYS))


def load_settings() -> Settings:
    return Settings(
        openai_api_key=os.getenv("OPENAI_API_KEY") or None,
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        rewiring_america_key=os.getenv("REWIRING_AMERICA_KEY") or None,
        dsire_key=os.getenv("DSIRE_KEY") or None,
    )


def ensure_output_dirs() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
