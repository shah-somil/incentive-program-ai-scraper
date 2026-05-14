# Dreamline AI — Tampa Incentives Scraper

Hybrid Python pipeline that produces `extracted_tampa_incentives.csv` for the
Dreamline AI incentive data project.  Uses APIs where available, traditional
scrapers for static HTML, and an OpenAI structured-output LLM parser for
unstructured / PDF content.

The deliverable schema (per `resources/Incentive Data Extraction Info-converted.md`):

```
program_name, state, city, incentive_type, property_type, description,
eligibility_criteria, incentive_amount, valid_until, updated_at,
review_needed, program_links
```

`incentive_type` is constrained to: `Grants | Rebates | Finance Solutions | Tax Credits | Investments`.

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env  # then fill in OPENAI_API_KEY (and optionally REWIRING_AMERICA_KEY)

# Produce the CSV
python -m dreamline_scraper.cli run -v

# Run the quality gates
python scripts/quality_gate.py

# Run unit tests
pytest
```

Outputs:

- `output/Extracted_Tampa_Incentives/extracted_tampa_incentives.csv` — the
deliverable.
- `output/logs/review_queue.csv` — every record where `review_needed = Yes`.
- `output/logs/run_<timestamp>.jsonl` — per-source counts and timings.

## Coverage

11 live scrapers + 3 catch-all "extras" sources covering federal, state,
utility, county, and city programs.  Most recent run produced 84 unique
records (target was 100+):


| Bucket                                             | Records |
| -------------------------------------------------- | ------- |
| Federal (IRS / IRA / DOE / HUD / VA / FEMA / USDA) | ~30     |
| Florida statewide                                  | ~20     |
| Hillsborough County / Tampa / surrounding MSA      | ~20     |
| TECO / Duke / Peoples Gas (utility)                | ~15     |


See `python -m dreamline_scraper.cli list-sources` for the full registry.

## Architecture

```
scrapers/   one BaseScraper subclass per source, each yielding RawIncentive
parsers/    OpenAI LLM parser for unstructured pages (lazy / optional)
extractors/ HTTP session (1 rps, retries, cache), HTML + PDF + Playwright helpers
validators/ Pydantic + completeness + amount sanity + optional URL HEAD checks
pipeline/   orchestrator -> dedupe -> writer (12-col CSV in exact column order)
```

The pipeline normalises every `RawIncentive` (the brief's 17-field schema)
into the leaner 12-column `IncentiveRecord` via `normalizer.to_record`.  Any
record missing a required CSV column, or carrying a low LLM confidence
score, is automatically flagged with `review_needed = "Yes"`.

## Live scraping vs. curated baselines

Most government / utility sites in scope are JavaScript-heavy or gated:

- DSIRE Florida loads its program list from an Angular SPA that calls a
paid-only API.  Without a DSIRE key the scraper falls back to a curated
set of the canonical Florida statewide programs.
- The Rewiring America public site requires a free API key for live calls.
Without one, the scraper falls back to canonical IRA federal programs.
- TECO, Duke, Florida Housing, Hillsborough, Tampa pages are scraped live
for additional rebate sentences when reachable; curated baselines fill in
the canonical numbers regardless.

Each scraper transparently merges live results with its curated fallback,
deduplicating on `(program_name, level, program_administrator)`.

## LLM parsing (OpenAI structured outputs)

When `OPENAI_API_KEY` is set, the LLM parser (`parsers/llm_parser.py`)
processes unstructured pages with a JSON-schema-enforced response format
(see `parsers/prompts.py`).  Records returned by the LLM are merged into the
pipeline; any with `confidence_score < 0.7` are flagged for review.

If no key is set, the LLM parser is silently disabled and only the curated

- static-scraping path runs.  This keeps the pipeline functional in offline
or CI environments.

## Quality gates

`scripts/quality_gate.py` runs against the produced CSV and asserts:

- Header is exactly the 12 required columns in order.
- `incentive_type` only uses `Grants / Rebates / Finance Solutions / Tax Credits / Investments`.
- `review_needed` is only `Yes` or `No`.
- `program_links` is populated for every row and starts with `http`.
- `program_name` is non-empty.
- `updated_at` is ISO format.
- Total records >= 60.

The integration test `tests/test_pipeline.py` enforces the same invariants
against an offline pipeline run.

Optional URL liveness checks: `python -m dreamline_scraper.cli run --check-links -1`.

## Known limitations / follow-ups

- DSIRE FL listing is JS-rendered behind a paid API.  Live discovery is
blocked; the curated state baseline is the source of truth until a DSIRE
key is provisioned (or Playwright is installed and used).
- Rewiring America requires a free API key for live use.  Sign up at
`https://docs.rewiringamerica.org/signin` and drop the key in `.env`.
- Playwright support is wired (see `extractors/playwright_runner.py`) but
the Chromium browser is not installed by default.  Install with
`python -m playwright install chromium` if you want JS-heavy sites
(FHFC, Duke, HCFL) to be rendered live.
- Several utility / city programs are intentionally flagged with
`confidence_score < 0.7` (e.g. Duke EV charger rebate, RenewPACE,
FRED, Habitat for Humanity, Manatee DPA).  Their canonical amounts vary
year-to-year and the review queue is the right place for a human to
confirm them against a fresh source page.
- Geographic scope is Tampa + Hillsborough + Tampa Bay MSA (Pinellas /
Pasco / Manatee).  Adding a new region requires only a new entry in
`_curated_expanded.local_extras` plus optional live scrapers.

## Reference materials

- `resources/Dreamline_AI_Brief_Incentives_Process-converted.md` — strategic
brief and 4-phase AI agent roadmap.
- `resources/Incentive Data Extraction Info-converted.md` — concrete CSV
task specification (column order, vocabulary, sources).

