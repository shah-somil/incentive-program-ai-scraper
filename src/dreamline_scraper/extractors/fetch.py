"""Unified page fetcher.

Returns plain text for any URL — HTML, PDF, or JS-rendered — so the LLM
parser does not need to care about transport.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from .html import make_soup, visible_text
from .http import PoliteSession, get_session
from .pdf import extract_pdf_text
from .playwright_runner import render_page

LOGGER = logging.getLogger(__name__)


# If a static fetch yields fewer than this many characters of visible text,
# we assume the page is JS-rendered and retry with Playwright.
_JS_FALLBACK_MIN_CHARS = 400


@dataclass
class FetchResult:
    text: str
    content_type: str  # "html_text" | "pdf_text" | "js_text" | "empty"
    final_url: str


def fetch(
    url: str,
    *,
    render: str = "auto",
    wait_selector: Optional[str] = None,
    timeout_ms: int = 45_000,
    session: Optional[PoliteSession] = None,
) -> FetchResult:
    """Fetch ``url`` and return plain text content.

    ``render`` is a hint from the source registry:
      - ``"static"``: only try the polite HTTP fetch.
      - ``"js"``:     skip straight to Playwright.
      - ``"auto"``:   try static, fall back to Playwright if text is sparse.

    ``wait_selector`` is forwarded to Playwright when used; the runner waits
    for that CSS selector before reading the rendered HTML.
    """

    session = session or get_session()

    if render != "js":
        static = _fetch_static(url, session)
        if static.text and (
            render == "static" or len(static.text) >= _JS_FALLBACK_MIN_CHARS
        ):
            return static
        if render == "static":
            return static

    rendered_html = render_page(
        url, timeout_ms=timeout_ms, wait_selector=wait_selector
    )
    if rendered_html:
        text = visible_text(make_soup(rendered_html))
        if text:
            return FetchResult(text=text, content_type="js_text", final_url=url)

    if render == "js":
        return FetchResult(text="", content_type="empty", final_url=url)
    return _fetch_static(url, session)


def _fetch_static(url: str, session: PoliteSession) -> FetchResult:
    try:
        resp = session.get(url)
    except Exception as exc:
        LOGGER.warning("fetch failed for %s: %s", url, exc)
        return FetchResult(text="", content_type="empty", final_url=url)

    if not resp.ok:
        LOGGER.warning("fetch %s returned %s", url, resp.status_code)
        return FetchResult(text="", content_type="empty", final_url=resp.url or url)

    final_url = resp.url or url
    ctype = (resp.headers.get("Content-Type") or "").lower()

    if "pdf" in ctype or final_url.lower().endswith(".pdf"):
        text = extract_pdf_text(resp.content) or ""
        return FetchResult(text=text, content_type="pdf_text", final_url=final_url)

    try:
        html = resp.text
    except Exception as exc:
        LOGGER.warning("decode failed for %s: %s", url, exc)
        return FetchResult(text="", content_type="empty", final_url=final_url)

    text = visible_text(make_soup(html))
    return FetchResult(text=text, content_type="html_text", final_url=final_url)
