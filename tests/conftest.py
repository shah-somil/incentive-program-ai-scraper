"""Shared pytest fixtures."""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


import pytest  # noqa: E402

from dreamline_scraper.config import Settings  # noqa: E402


@pytest.fixture
def offline_settings() -> Settings:
    return Settings()
