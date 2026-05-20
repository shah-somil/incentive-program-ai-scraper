from __future__ import annotations

from dreamline_scraper.url_utils import coerce_http_url, is_http_url, resolve_program_link


def test_is_http_url():
    assert is_http_url("https://example.com/path")
    assert not is_http_url("ftp://example.com")
    assert not is_http_url("not a url")


def test_coerce_http_url_adds_scheme():
    assert coerce_http_url("RebuildingForTomorrow.HCFL.gov") == (
        "https://RebuildingForTomorrow.HCFL.gov"
    )


def test_resolve_program_link_prefers_application():
    assert resolve_program_link(
        "https://apply.example.com",
        "https://source.example.com",
    ) == "https://apply.example.com"


def test_resolve_program_link_falls_back_to_source():
    assert resolve_program_link("not a url", "https://source.example.com") == (
        "https://source.example.com"
    )


def test_resolve_program_link_invalid_application_uses_source():
    assert resolve_program_link("/relative/path", "https://irs.gov/credits") == (
        "https://irs.gov/credits"
    )
