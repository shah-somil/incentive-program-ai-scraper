"""Lazy Playwright runner for JavaScript-heavy sites.

Playwright is treated as an optional dependency so the bulk of the pipeline
runs even when the user has not installed browsers.
"""

from __future__ import annotations

import logging
from typing import Optional

LOGGER = logging.getLogger(__name__)


def render_page(
    url: str,
    *,
    timeout_ms: int = 45000,
    wait_selector: Optional[str] = None,
    wait_until: str = "domcontentloaded",
) -> Optional[str]:
    """Return rendered HTML for ``url`` or ``None`` if Playwright is unavailable.

    Defaults changed from the original (``networkidle`` + 20s) to
    ``domcontentloaded`` + 45s because many government / utility sites have
    long-tail network calls (analytics, chat widgets) that prevent
    ``networkidle`` from ever firing.  We instead anchor on the DOM being
    parsed and then optionally wait for ``wait_selector`` to confirm the
    interesting markup has been hydrated.
    """

    try:
        from playwright.sync_api import sync_playwright  # type: ignore
    except ImportError:
        LOGGER.warning("playwright not installed; skipping JS render for %s", url)
        return None
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            try:
                page = browser.new_page(
                    user_agent=(
                        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/130.0.0.0 Safari/537.36"
                    )
                )
                page.goto(url, timeout=timeout_ms, wait_until=wait_until)
                if wait_selector:
                    try:
                        page.wait_for_selector(wait_selector, timeout=timeout_ms)
                    except Exception:  # pragma: no cover - selector timing
                        pass
                return page.content()
            finally:
                browser.close()
    except Exception as exc:  # pragma: no cover - browser environment
        LOGGER.warning("playwright render failed for %s: %s", url, exc)
        return None
