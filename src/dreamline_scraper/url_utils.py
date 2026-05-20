"""URL helpers for source registry and program_links normalization."""

from __future__ import annotations

import re
from typing import Optional
from urllib.parse import urlparse

_SCHEME_RE = re.compile(r"^https?://", re.I)


def is_http_url(url: Optional[str]) -> bool:
    if not url or not str(url).strip():
        return False
    parsed = urlparse(str(url).strip())
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


def coerce_http_url(url: Optional[str]) -> Optional[str]:
    """Return an absolute http(s) URL, or None if the value is not recoverable."""

    if not url:
        return None
    cleaned = " ".join(str(url).split())
    if not cleaned:
        return None
    if _SCHEME_RE.match(cleaned):
        return cleaned if is_http_url(cleaned) else None
    # Bare host/path often emitted by the LLM (e.g. RebuildingForTomorrow.HCFL.gov).
    if " " in cleaned or len(cleaned) < 4 or cleaned.startswith("/"):
        return None
    if "." not in cleaned.split("/")[0]:
        return None
    candidate = f"https://{cleaned.lstrip('/')}"
    return candidate if is_http_url(candidate) else None


def resolve_program_link(
    application_url: Optional[str],
    source_url: Optional[str],
) -> str:
    """Pick program_links: prefer a valid application URL, else the scraped page."""

    for candidate in (application_url, source_url):
        normalized = coerce_http_url(candidate)
        if normalized:
            return normalized
    return (source_url or "").strip()
