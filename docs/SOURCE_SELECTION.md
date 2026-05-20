# Source selection (`sources.py`)

The pipeline no longer uses hand-typed curated program records (`_curated.py` was
removed). **`src/dreamline_scraper/sources.py` is the only registry of where to
scrape.** Every row in the CSV is extracted live from these pages via the LLM.

## How sources were chosen

Selection follows the kickoff brief ([`resources/Dreamline_AI_Brief_Incentives_Process-converted.md`](../resources/Dreamline_AI_Brief_Incentives_Process-converted.md) §3.3) and the extraction task spec ([`resources/Incentive Data Extraction Info-converted.md`](../resources/Incentive%20Data%20Extraction%20Info-converted.md)):

| Priority | Brief source | `sources.py` entry | Notes |
| --- | --- | --- | --- |
| P0 | DSIRE Florida | `DSIRE — Florida programs` | `programs.dsireusa.org` SPA; `render=js` |
| P0 | Rewiring America IRA | `Rewiring America — Federal Incentives` | Public page at `homes.rewiringamerica.org` (IRA calculator is interactive; this page lists federal programs) |
| P0 | TECO rebates | `TECO (Tampa Electric) — Save Energy hub` | Brief URL moved; current hub is `/residential/saveenergy/` |
| P1 | My Safe Florida Home | `My Safe Florida Home` | `mysafeflhome.com` (current domain) |
| P1 | IRS energy credits | Multiple IRS credit pages | Split into hub + 25C, 25D, 30C, 30D, 25E for clearer extraction |
| P1 | Florida Housing | FHFC programs + homebuyer overview | JS-rendered |
| P1 | Hillsborough housing | `Hillsborough County — Residents portal` | `hcfl.gov/residents` aggregates housing programs |
| P1 | Duke Energy FL | `Duke Energy Florida — Home Products` | Browser UA required (403 on scraper UA) |
| P2 | City of Tampa | `City of Tampa — Housing & Community Development` | |
| P2 | FEMA mitigation | HMGP, BRIC, Flood Mitigation pages | |
| P2 | PACE (Ygrene / RenewPACE / FRED) | Three dedicated sources | Brief listed `fredelocal.com` (dead); FRED is at `flcpace.org` |

**Geography:** Federal + Florida statewide programs, then Hillsborough/Tampa (primary market), plus Pinellas, Pasco, and Manatee county portals for Tampa Bay MSA coverage.

**Extras beyond the brief table:** DOE Weatherization, HUD 203(k), USDA Section 504, VA home loans, Peoples Gas, FL DOR exemptions, Florida PACE Funding Agency — added because they appear in the extraction spec’s government/utility lists and fill common homeowner upgrade categories.

## What we intentionally do *not* scrape here

- **DSIRE paid API** — listing page is scraped; bulk API requires registration.
- **Rewiring America API** — optional future integration; not required for CSV delivery.
- **Third-party aggregators** — excluded to keep `program_links` traceable to primary sources.

## Promoting a new source

1. Confirm the page is public, allowed by `robots.txt`, and describes active programs.
2. Add a `Source(...)` block to `sources.py` with correct `level` and jurisdiction hints.
3. Run `PYTHONPATH=src python scripts/validate_sources.py` to confirm the URL is live.
4. Run a targeted extraction: `python -m dreamline_scraper.cli run --source "Your Source" -v`.

## Review cadence

Re-run `scripts/validate_sources.py` after any source URL change or quarterly. Government sites frequently reorganize paths; the audit log (`output/logs/run_*.jsonl`) surfaces fetch regressions (`text_chars: 0`).
