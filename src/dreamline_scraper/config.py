"""Runtime configuration: output paths + environment-driven settings."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

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


@dataclass
class Settings:
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o-mini"
    user_agent: str = (
        "DreamlineAI-Scraper/0.2 (+https://dreamlineai.org/scraper) "
        "research-data-collection"
    )
    request_min_interval_s: float = 1.0
    http_timeout_s: float = 30.0


def load_settings() -> Settings:
    return Settings(
        openai_api_key=os.getenv("OPENAI_API_KEY") or None,
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
    )


def ensure_output_dirs() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
