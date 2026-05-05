"""Test DSIRE detail-page parser using a synthetic fixture."""

from __future__ import annotations

from dreamline_scraper.scrapers.dsire_florida import DSIREFloridaScraper


_DETAIL_HTML = """
<html><body>
<h1>Florida Renewable Energy Property Tax Exemption</h1>
<p>Tax Exemption / Property Tax Incentive</p>
<p>Incentive Amount: 100% of the assessed value attributable to a renewable
energy source device is exempt from property tax.</p>
<p>Administered by: Florida Department of Revenue</p>
</body></html>
"""


def test_dsire_detail_parser_extracts_program_name_and_amount(offline_ctx):
    scraper = DSIREFloridaScraper(ctx=offline_ctx)
    record = scraper._parse_detail(
        _DETAIL_HTML,
        "https://programs.dsireusa.org/system/program/detail/123",
    )
    assert record is not None
    assert "Renewable Energy Property Tax Exemption" in record.program_name
    assert record.program_administrator == "Florida Department of Revenue"
    assert record.source_url.endswith("/123")
