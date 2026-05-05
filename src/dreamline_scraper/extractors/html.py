"""BeautifulSoup helpers used across scrapers."""

from __future__ import annotations

import re
from typing import Optional

from bs4 import BeautifulSoup


_WHITESPACE_RE = re.compile(r"\s+")


def make_soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "lxml")


def clean_text(value: Optional[str]) -> str:
    """Collapse whitespace and trim. Returns ``""`` if value is falsy."""

    if not value:
        return ""
    return _WHITESPACE_RE.sub(" ", value).strip()


def visible_text(soup: BeautifulSoup) -> str:
    """Extract human-readable text from a BeautifulSoup tree."""

    for tag in soup(["script", "style", "noscript", "header", "footer", "nav"]):
        tag.decompose()
    return clean_text(soup.get_text(" "))
