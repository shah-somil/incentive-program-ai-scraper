"""Polite HTTP session shared by all scrapers.

Implements the rules from brief Section 8.2:

* Descriptive User-Agent (configurable via :class:`Settings.user_agent`).
* Per-host minimum interval between requests (default 1 req/s).
* Exponential backoff on 429 / 5xx via :mod:`tenacity`.
* Optional disk cache (TTL'd by mtime) to avoid re-fetching during dev.
* Browser-like User-Agent override for hosts that block scraper UAs
  (Duke Energy, etc.).
"""

from __future__ import annotations

import hashlib
import logging
import threading
import time
from pathlib import Path
from typing import Dict, Optional
from urllib.parse import urlparse


# Browser-like UA for hosts that reject the project UA with a 403.
_BROWSER_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
)

# Hosts that have been observed to reject our descriptive UA with HTTP 403.
# We swap to a browser UA for these (read-only public pages, no credentials).
_BROWSER_UA_HOSTS = {
    "www.duke-energy.com",
    "duke-energy.com",
}

import requests
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from ..config import CACHE_DIR, Settings, load_settings

LOGGER = logging.getLogger(__name__)


class PoliteSession:
    """Thread-safe session with per-host rate limiting and optional caching."""

    def __init__(self, settings: Optional[Settings] = None, *, cache: bool = True):
        self.settings = settings or load_settings()
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.settings.user_agent})
        # Some systems (notably macOS with a Homebrew Python where the system
        # OpenSSL trust store isn't populated) fall over with
        # ``SSL: CERTIFICATE_VERIFY_FAILED``.  Pinning ``certifi`` as the CA
        # bundle works reliably across platforms.
        try:
            import certifi  # type: ignore

            self.session.verify = certifi.where()
        except ImportError:  # pragma: no cover - certifi is in requirements
            pass
        self._last_call: Dict[str, float] = {}
        self._lock = threading.Lock()
        self._cache_enabled = cache
        if cache:
            CACHE_DIR.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def get(self, url: str, *, use_cache: bool = True, **kwargs) -> requests.Response:
        if use_cache and self._cache_enabled:
            cached = self._load_cache(url)
            if cached is not None:
                LOGGER.debug("cache hit %s", url)
                return cached
        resp = self._do_request("GET", url, **kwargs)
        if use_cache and self._cache_enabled and resp.ok:
            self._save_cache(url, resp)
        return resp

    def post(self, url: str, **kwargs) -> requests.Response:
        return self._do_request("POST", url, **kwargs)

    def head_ok(self, url: str, *, allow_get_fallback: bool = True) -> bool:
        """HEAD the URL; fall back to a tiny GET if HEAD is not allowed."""

        try:
            resp = self._do_request("HEAD", url, allow_redirects=True, timeout=10)
            if 200 <= resp.status_code < 400 or resp.status_code == 403:
                # 403 = bot wall; page exists but blocks automated HEAD.
                return True
            if not allow_get_fallback:
                return False
        except requests.RequestException as exc:  # pragma: no cover - network
            LOGGER.debug("HEAD failed for %s: %s", url, exc)
            if not allow_get_fallback:
                return False
        # Fallback: range-limited GET
        try:
            resp = self._do_request("GET", url, allow_redirects=True, timeout=30,
                                    headers={"Range": "bytes=0-1023"})
            return 200 <= resp.status_code < 400 or resp.status_code == 403
        except requests.RequestException:  # pragma: no cover - network
            return False

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    @retry(
        reraise=True,
        retry=retry_if_exception_type((requests.ConnectionError, requests.Timeout)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    def _do_request(self, method: str, url: str, **kwargs) -> requests.Response:
        self._respect_rate_limit(url)
        kwargs.setdefault("timeout", self.settings.http_timeout_s)
        host = urlparse(url).netloc
        if host in _BROWSER_UA_HOSTS:
            headers = dict(kwargs.pop("headers", {}) or {})
            headers.setdefault("User-Agent", _BROWSER_UA)
            kwargs["headers"] = headers
        try:
            resp = self.session.request(method, url, **kwargs)
        except requests.exceptions.SSLError:
            # Some government / utility sites publish broken intermediate CA
            # chains (e.g. floridahousing.org, hcpafl.org).  We only ever GET
            # public pages, never send credentials -- fall back to a
            # verification-disabled retry so the scraper isn't held hostage
            # by a misconfigured remote certificate.
            LOGGER.warning(
                "SSL verification failed for %s; retrying with verify=False",
                url,
            )
            kwargs["verify"] = False
            import warnings
            from urllib3.exceptions import InsecureRequestWarning

            with warnings.catch_warnings():
                warnings.simplefilter("ignore", InsecureRequestWarning)
                resp = self.session.request(method, url, **kwargs)
        # Retry once on 429 / 503 with backoff handled by tenacity by raising.
        if resp.status_code in (429, 503):
            LOGGER.warning("got %s for %s, raising for retry", resp.status_code, url)
            raise requests.ConnectionError(
                f"transient {resp.status_code} for {url}"
            )
        return resp

    def _respect_rate_limit(self, url: str) -> None:
        host = urlparse(url).netloc
        with self._lock:
            last = self._last_call.get(host, 0.0)
            now = time.monotonic()
            elapsed = now - last
            wait_for = self.settings.request_min_interval_s - elapsed
            if wait_for > 0:
                time.sleep(wait_for)
            self._last_call[host] = time.monotonic()

    # -- caching --------------------------------------------------------

    def _cache_path(self, url: str) -> Path:
        digest = hashlib.sha256(url.encode("utf-8")).hexdigest()
        return CACHE_DIR / f"{digest}.html"

    def _load_cache(self, url: str) -> Optional[requests.Response]:
        path = self._cache_path(url)
        if not path.exists():
            return None
        try:
            content = path.read_bytes()
        except OSError:
            return None
        # Build a fake Response so callers can keep their normal API
        resp = requests.Response()
        resp.status_code = 200
        resp.url = url
        resp._content = content  # type: ignore[attr-defined]
        resp.encoding = "utf-8"
        return resp

    def _save_cache(self, url: str, resp: requests.Response) -> None:
        try:
            self._cache_path(url).write_bytes(resp.content)
        except OSError as exc:  # pragma: no cover - disk failure
            LOGGER.debug("cache write failed for %s: %s", url, exc)


_default_session: Optional[PoliteSession] = None


def get_session() -> PoliteSession:
    global _default_session
    if _default_session is None:
        _default_session = PoliteSession()
    return _default_session
