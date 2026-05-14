**Section 1- 2 — What We Are Building & Why It Matters**

## 2.1 The Product — Dreamline AI

Dreamline AI is a property intelligence platform that helps property owners — homeowners, investors, landlords, and commercial operators — discover every available incentive program for their specific property and connect with vetted contractors to execute the upgrades.

| **Platform URL** | dreamlineai.org |
| --- | --- |
| **Launch Market** | Tampa, Florida — expanding to all Florida ZIP codes |
| **Core Feature** | Enter your address → instantly see every incentive, tax credit, grant, and zero-down financing option available for your property |
| **Secondary Feature** | Match with vetted local contractors for the specific project |
| **Organization** | Community Dream Foundation (CDF) |

## 2.2 The Problem We Are Solving

The incentive gap is massive. Hundreds of programs exist at the federal, state, county, city, and utility level. But the information is fragmented, buried in government websites, and written in language most homeowners cannot parse. The result:

* Billions in federal IRA clean energy credits go unclaimed every year
* Florida's My Safe Florida Home hurricane grant program — up to $10,000 — most eligible homeowners have never heard of it
* PACE zero-down financing exists for solar, HVAC, and roofing — most contractors don't mention it because homeowners don't ask
* Utility rebates from TECO and Duke Energy expire unclaimed because homeowners don't know the deadline

| KEY INSIGHT: The problem is not the availability of incentives — it is the discovery gap.  Dreamline AI is the infrastructure that closes that gap. Our data pipeline is the foundation. |
| --- |

## 2.3 Why Tampa Bay First

* 1.3 million housing units in the Tampa Bay MSA — large immediate market
* High renovation activity driven by hurricane resilience investments post-2023/2024 seasons
* TECO and Duke Energy both have active rebate programs — real immediate value for homeowners
* Florida net metering rates are declining after 2026 — urgency window drives solar demand now
* Hillsborough County SHIP program provides rehabilitation grants for income-qualified homeowners
* City of Tampa has approved an $11.4M residential rehabilitation JOC program — active contractor demand

**Section 3 — Current Manual Workflow (Phase 1)**

| This is how we work RIGHT NOW — before AI automation. The manual phase is not a placeholder.  It teaches us the data structure, the edge cases, and the source quality issues that will  inform everything we automate later. Do this phase carefully. |
| --- |

## 3.1 The Six-Step Manual Pipeline

| **Step** | **Activity** | **Tool / Method** | **Output** |
| --- | --- | --- | --- |
| 1 | Identify incentive sources for Tampa/Hillsborough | Research — DSIRE, Google, gov sites | Source list with URLs |
| 2 | Visit each source and read program details | Manual browser + notes | Raw program notes |
| 3 | Extract structured fields for each program | Google Sheets / Airtable / Notion | Structured data rows |
| 4 | Validate data — check amounts, eligibility, deadlines | Cross-reference source + IRS/gov PDFs | Validated records |
| 5 | Load structured data to platform database | CSV upload or direct DB entry | Live incentive records |
| 6 | Set reminder to re-check each source for updates | Calendar / task manager | Refresh schedule |

## 3.2 Required Data Fields — Every Program Must Have These

| **Field Name** | **Description** | **Example Value** | **Required** |
| --- | --- | --- | --- |
| program\_name | Official name of the incentive program | Residential Clean Energy Credit | Yes |
| category | Type: solar / hvac / roof / window / general | solar | Yes |
| type | tax\_credit / grant / rebate / loan / financing | tax\_credit | Yes |
| level | federal / state / county / city / utility | federal | Yes |
| amount\_type | fixed\_dollar / percentage / per\_unit / up\_to | percentage | Yes |
| amount\_value | Dollar amount or percentage | 30 | Yes |
| amount\_max | Maximum cap if applicable | $2,000 | If applicable |
| eligible\_property\_types | SFH / condo / multifamily / commercial / all | all | Yes |
| eligible\_project\_types | What upgrade types qualify | solar, battery, wind | Yes |
| zip\_codes | Specific ZIPs or leave blank for statewide | 33602, 33603 OR statewide | Yes |
| income\_required | Does the program have income limits? | Yes — 80% AMI | Yes |
| requires\_homeownership | Owner-occupied only? | Yes | Yes |
| eligibility\_notes | Any other special requirements | Must file Form 5695 with taxes | If applicable |
| application\_url | Direct URL to apply or learn more | https://irs.gov/form5695 | Yes |
| program\_administrator | Who runs the program | IRS / Florida DFS / TECO | Yes |
| source\_url | URL where data was found | dsireusa.org/florida | Yes |
| expires\_at | Program end date if known | 2032-12-31 | If known |
| last\_verified\_at | Date this record was last checked | 2026-04-01 | Yes |

## 3.3 Priority Sources to Scrape in Phase 1

| **Priority** | **Source** | **URL** | **Programs Expected** |
| --- | --- | --- | --- |
| P0 | DSIRE Florida | dsireusa.org — filter by FL | 30–50 state/utility programs |
| P0 | Rewiring America IRA Tool | rewiringamerica.org/app/ira-calculator | All federal IRA programs |
| P0 | TECO Rebates | tampaelectric.com/home/save-energy/rebates | 5–10 utility programs |
| P1 | My Safe Florida Home | mysafefloridahome.com | Hurricane grant program |
| P1 | IRS Energy Credits | irs.gov/credits-deductions/energy-tax-credits | 25C + 25D federal credits |
| P1 | Florida Housing Finance Corp | floridahousing.org/programs | SHIP, HOME, DPA programs |
| P1 | Hillsborough County Housing | hillsboroughcounty.org/housing | SHIP, CDBG programs |
| P1 | Duke Energy Florida | duke-energy.com/home/products/rebates | 3–6 utility programs |
| P2 | City of Tampa Community Dev | tampa.gov/community-development | Local rehab programs |
| P2 | FEMA Hazard Mitigation | fema.gov/grants/mitigation | HMGP, BRIC programs |
| P2 | Ygrene / RenewPACE / FRED | ygrene.com / renewpace.com / fredelocal.com | PACE financing programs |

# Section 4 — AI Agent Explanation

| This section explains the AI automation vision to your team — both the technical and  non-technical members. Use these explanations during the call to build alignment on  where we are going after the manual phase is complete. |
| --- |

## 4.1 What an AI Agent Is — Simple Explanation

An AI agent is a software system that perceives inputs, makes decisions, takes actions, and learns from the results — without a human directing each individual step. For our use case, instead of a data engineer manually visiting a government website and copying program details into a spreadsheet, the AI agent does this automatically, continuously, and at scale.

Think of it as hiring a research team that works 24 hours a day, never takes breaks, and automatically flags anything that changes — then asks a human only when it encounters something genuinely ambiguous.

## 4.2 The Five Components of Our Incentive AI Agent

| **Component** | **What It Does** | **Technology** |
| --- | --- | --- |
| Crawler / Discoverer | Finds new incentive sources — government sites, utility pages, news articles announcing new programs. Monitors a curated list of known sources plus discovers new ones via search. | Python Scrapy, Playwright, Google Search API, Common Crawl |
| Extractor | Visits each source and extracts raw content — HTML text, PDF documents, tables. Handles JavaScript-heavy sites that basic scrapers cannot read. | Playwright/Puppeteer, pdfplumber, BeautifulSoup, Trafilatura |
| Parser / Normalizer | Sends raw extracted text to an LLM (large language model) with a structured prompt. The LLM reads the unstructured content and outputs a clean JSON record matching our data schema. | GPT-4o / Claude 3.5 via API, structured output / function calling |
| Validator | Checks the LLM output for completeness, accuracy, and internal consistency. Flags missing required fields, amount anomalies, and expired programs for human review. | Python validation layer, Pydantic schema validation, human review queue |
| Updater / Monitor | Re-visits all known sources on a schedule. Compares new extractions against stored records. Flags changes, expiries, and new programs. Triggers alerts when funding runs out or deadlines pass. | Celery + Redis scheduler, diff logic, Slack/email alerting |

## 4.3 LLMs vs Traditional Scraping — When to Use Which

| **Situation** | **Best Approach** | **Why** |
| --- | --- | --- |
| Structured table on government site | Traditional scraper (BeautifulSoup/Scrapy) | Fast, cheap, reliable — no need for LLM |
| PDF document with program details | PDF extractor + LLM parser | LLMs excel at reading unstructured PDFs |
| JavaScript-heavy page (React/Angular) | Playwright headless browser + LLM | Browser renders JS; LLM extracts meaning |
| Inconsistent formats across sources | LLM with structured output prompt | LLMs normalize variation automatically |
| Detecting if a program changed | Hash comparison + LLM diff summary | LLM summarizes what changed in plain English |
| New source discovery | LLM + web search agent | LLM can evaluate if a new URL is relevant |
| Amount validation / sanity check | Rule-based validator | Rules are faster and more reliable for numbers |

## 4.4 Structured Pipelines vs Autonomous Agents

**Structured Pipeline:** A fixed sequence of steps — crawl → extract → parse → validate → store. Predictable, testable, and easier to debug. Best for Phase 1 and Phase 2 of our build.

**Autonomous Agent:** An AI that can decide its own next action, loop back if validation fails, search for new sources when it cannot find data, and adapt to changing website structures. More powerful but harder to control. Best for Phase 3 and Phase 4.

| RECOMMENDATION: Start with structured pipelines. Build autonomous agent capabilities on top  once the pipeline is stable and the data quality is validated. Do not skip the pipeline phase. |
| --- |

# Section 5 — System Architecture Overview

## 5.1 High-Level Architecture — Four Layers

| **Layer** | **Name** | **Components** | **Purpose** |
| --- | --- | --- | --- |
| Layer 1 | Data Ingestion | Crawlers, scrapers, PDF extractors, API clients (DSIRE, Rewiring America, HCPA) | Collect raw data from all incentive sources |
| Layer 2 | Processing & Normalization | LLM parser, schema validator, deduplication engine, ZIP code mapper | Transform raw content into structured, clean records |
| Layer 3 | AI / Agent Layer | Orchestrator agent, source discovery agent, change detection agent, review queue | Automate discovery, extraction, and monitoring at scale |
| Layer 4 | Storage & Delivery | PostgreSQL (incentives DB), Redis (cache), REST API, dreamlineai.org platform | Store validated data and serve it to end users instantly |

## 5.2 Data Flow Diagram — Text Representation

| SOURCE DISCOVERY  DSIRE API → Pull Florida programs  Rewiring America API → Pull federal IRA programs  TECO / Duke / FHFC websites → Web scraper  New sources → AI Discovery Agent searches for new programs  ↓  RAW EXTRACTION  HTML pages → BeautifulSoup / Scrapy  JS-heavy pages → Playwright headless browser  PDF documents → pdfplumber + text extraction  ↓  LLM PARSING (Claude / GPT-4o)  Prompt: Extract incentive program details → Output: JSON matching our schema  Structured output enforced via function calling / JSON mode  ↓  VALIDATION LAYER  Pydantic schema validation → Flag missing required fields  Amount sanity check → Flag outliers (e.g., $0 or $99,000,000)  Expiry check → Flag programs past their deadline  Confidence score → Low confidence → Human review queue  ↓  STORAGE — PostgreSQL  incentive\_programs table (validated records)  property\_parcels table (HCPA property data by ZIP)  scrape\_logs table (audit trail for every extraction)  ↓  API LAYER — FastAPI / Node.js  GET /api/incentives?zip=33602  GET /api/incentives?address=123+Main+St+Tampa+FL  GET /api/incentives?address=...&income=75000&household\_size=3  ↓  DREAMLINE AI PLATFORM  User enters address → Instant incentive results  Assessment results → Personalized ranked incentive list  Contractor matching → Connect with vetted local pros |
| --- |

## 5.3 Technology Stack Recommendation

| **Category** | **Recommended Tool** | **Purpose** | **Cost** |
| --- | --- | --- | --- |
| Scraping (static) | Python + Requests + BeautifulSoup | Fast scraping of standard HTML pages | Free |
| Scraping (dynamic JS) | Playwright (Python) | Render JavaScript-heavy government sites | Free |
| Large-scale crawling | Scrapy | Structured, scalable scraping framework | Free |
| PDF extraction | pdfplumber + PyMuPDF | Extract text from government PDF documents | Free |
| LLM parsing | Claude claude-sonnet-4-20250514 or GPT-4o | Normalize unstructured content to schema JSON | ~$0.01–0.05/page |
| Schema validation | Pydantic (Python) | Enforce data types and required fields | Free |
| Job scheduling | Celery + Redis | Schedule scraping jobs, manage refresh cycles | Free (self-hosted) |
| Primary database | PostgreSQL | Store all incentive and property records | Free (self-hosted) |
| Caching layer | Redis | Cache ZIP-level incentive lookups (TTL 24h) | Free (self-hosted) |
| API framework | FastAPI (Python) | Serve incentive data to the platform | Free |
| Geocoding | Google Maps API / Census Geocoder | Address to coordinates / census tract | Free tier + paid |
| Property data | Hillsborough County HCPA API | Property details by address/parcel | Free (public) |
| DSIRE incentive data | DSIRE API | Comprehensive FL incentive database | Free (API key req.) |
| IRA incentive data | Rewiring America API | Federal IRA personalized incentives | Free tier |
| Monitoring | Sentry + Grafana | Error tracking + data freshness dashboards | Freemium |

# Section 6 — Step-by-Step AI Agent Build Plan (4 Phases)

This is the roadmap from manual scraping today to a fully autonomous AI agent. Each phase builds on the previous one. Do not skip phases — the data quality and architecture lessons from each phase inform the next.

| **Phase 1: Assisted Scraping — Manual + Tooling (Weeks 1–4)**   * Human researchers identify incentive sources and visit each one * Data entry standardized using the Dreamline AI schema template (Google Sheets → CSV) * Python scripts built to automate repetitive scraping tasks (DSIRE API, TECO rebate page) * Rewiring America API integrated to cover all federal IRA programs automatically * HCPA property data bulk download loaded to PostgreSQL * First version of GET /api/incentives?zip= endpoint built and tested * Team learns the data: what fields are hard to find, what sources are unreliable, what breaks * DELIVERABLE: 150+ validated incentive records covering all Tampa Bay ZIP codes |
| --- |

| **Phase 2: Semi-Automated Pipelines — Scheduled + Structured (Weeks 5–10)**   * Build Scrapy spiders for top 10 incentive sources — scheduled to run weekly * Build Playwright scrapers for JavaScript-heavy sites (Florida Housing, utility portals) * Implement LLM parser: send extracted HTML/text to Claude/GPT-4o → receive structured JSON * Build Pydantic validation layer — auto-flag incomplete or anomalous records * Build human review queue — flagged records sent to Airtable/Notion for manual approval * Build diff engine — compare new scrape output to stored records, flag changes * Set up Celery scheduler — weekly scrape of all sources, monthly deep refresh * DELIVERABLE: 95% of incentive records auto-updated, < 5% require human review |
| --- |

| **Phase 3: Intelligent Agents — Adaptive and Self-Correcting (Weeks 11–18)**   * Build Source Discovery Agent: uses LLM + web search to find new incentive programs not in current database * Build Extraction Agent: chooses scraping method automatically (static vs dynamic) based on site analysis * Build Validation Agent: uses LLM to cross-reference scraped data against secondary sources * Build Change Alert Agent: monitors sources for program updates, funding exhaustion, new programs * Implement confidence scoring: LLM rates its own extraction confidence; low-confidence → human review * Build feedback loop: human corrections to the review queue train the parser to improve over time * DELIVERABLE: Full pipeline runs with minimal human involvement; team reviews exceptions only |
| --- |

| **Phase 4: Self-Updating System — Fully Autonomous (Weeks 19+)**   * System discovers, scrapes, validates, and stores new incentive programs without human initiation * Multi-state expansion: agent adapts to new state's incentive structure without code changes * Real-time monitoring: system detects when a TECO rebate amount changes and updates within hours * Proactive alerts to users: 'The program you qualified for is expiring in 30 days — act now' * API licensed to third parties: real estate apps, mortgage lenders, property management platforms * DELIVERABLE: Platform covers all Florida ZIP codes; data freshness guaranteed within 24 hours |
| --- |

# Section 7 — Talking Points for the Team

## 7.1 Alignment Points — Start the Call With These

* We are building a data-first product. The quality of our incentive data IS the quality of the product. Take this phase seriously.
* Phase 1 is not a delay — it is research. Every edge case we find manually makes our AI smarter.
* We are not just scraping data. We are understanding the structure of incentive programs so we can automate their discovery.
* Every team member's observations during manual scraping will be used to improve the AI agent design.

## 7.2 Setting Expectations

* The manual phase will be tedious in places — that is expected. Document every challenge because those are automation targets.
* Some government websites are poorly designed, load slowly, or change without warning — build in error handling from day one.
* We expect 10–15% of scraped records to require manual review even after automation. That is normal.
* Data freshness matters. An expired incentive shown to a homeowner damages trust. Build staleness alerts into your thinking from the start.

## 7.3 Defining Responsibilities

| **Role** | **Responsibilities** | **Phase 1 Deliverable** |
| --- | --- | --- |
| Data Engineers | Build and maintain the database schema. Design the scraping pipeline architecture. Write the validation layer. Own data quality. | Schema deployed, DSIRE + Rewiring America APIs integrated, 150+ records loaded |
| Web Scrapers | Execute manual scraping of all priority sources. Build automated spiders for repeating sources. Document scraping challenges and site structures. | All P0 and P1 sources scraped, data in standardized template, scraping notes documented |
| AI Agent Builders | Research LLM parsing approaches. Build the extraction prompt template. Prototype the LLM parser on 10 real scraped examples. Design the agent architecture. | LLM parser prototype working on 10 sample pages, architecture doc drafted |
| Product / Project Lead | Prioritize sources and program categories. QA final records for accuracy. Liaise with property owners and contractors to validate which incentives matter most. | Source priority list approved, 20 records manually QA'd, contractor feedback documented |

## 7.4 Questions to Ask the Team During the Call

* Data Engineers: What database have you used before for this type of pipeline? Any concerns with PostgreSQL + Redis?
* Scrapers: Have you worked with government sites before? What has been the biggest challenge with public data scraping?
* AI Builders: What LLM API have you used? Do you have experience with structured output / function calling?
* Everyone: What do you need from me in Week 1 to unblock your work?

# Section 8 — Risks & Considerations

## 8.1 Data Risks

| **Risk** | **Likelihood** | **Impact** | **Mitigation** |
| --- | --- | --- | --- |
| Incentive program changes without notice | High | High | Weekly scrape schedule + change detection diff engine. Alert on any amount or eligibility change. |
| Program funding exhausted mid-year | Medium | High | Monitor program pages for 'closed' or 'paused' language. Flag programs with limited funding pools. |
| Data inconsistency across sources | High | Medium | Always cross-reference amounts against IRS.gov or official state statutes. Primary source wins. |
| Duplicate programs from multiple sources | High | Low | Deduplication logic keyed on program\_name + level + administrator. LLM to detect near-duplicates. |
| LLM hallucination — incorrect field values | Medium | High | Validation layer catches outliers. Human review queue for low-confidence records. Never trust LLM amounts without source verification. |
| Historical data loss on program update | Medium | Medium | Maintain full audit log of all record changes in scrape\_logs table. Never overwrite — always version. |

## 8.2 Legal & Ethical Scraping Considerations

* **Always check robots.txt:** Before building any scraper, check the site's robots.txt. Disallowed paths must not be scraped.
* **Use APIs where available:** DSIRE, Rewiring America, HCPA, and Census all have public APIs. Use those instead of scraping wherever possible.
* **Rate limiting:** No more than 1 request per second to any government site. Implement exponential backoff on errors. Be a polite crawler.
* **Terms of Service:** Review ToS for commercial API usage. DSIRE and Rewiring America may require attribution or have commercial use restrictions.
* **Data attribution:** Display source name and link for every incentive program shown on the platform. Give credit to the program administrators.
* **Personal data:** User addresses, income, and household data collected during assessment must be encrypted at rest and in transit. Never log personal data in scraping infrastructure.

## 8.3 Scaling Risks

* **State-by-state variation:** Every state has different incentive structures, PACE laws, and utility territories. Build the schema to be state-agnostic from day one.
* **Utility territory complexity:** TECO and Duke serve different ZIP codes in Tampa Bay — some parcels are on the boundary. Build utility territory matching into property profiles.
* **Program complexity:** Some programs have stacking rules, income tiers, or property-age requirements. The schema must support all variations.
* **Team scaling:** As the platform expands to new regions, the manual scraping team grows before AI takes over. Document everything so new scrapers can onboard in < 1 day.

| **PART B**  **STANDARD OPERATING PROCEDURE**  *Internal documentation for data engineers, scrapers, and AI builders* |
| --- |

# Section 9 — SOP Overview & Purpose

| DOCUMENT PURPOSE: This Standard Operating Procedure defines the processes, roles, data standards,  and quality guidelines for the Dreamline AI Incentive Data Pipeline. All team members working on  data collection, processing, or AI automation must read and follow this document.  Version: 1.0 | Owner: Engineering Lead | Review Cycle: Monthly |
| --- |

## 9.1 What This SOP Covers

* The complete data pipeline from source discovery to platform delivery
* Manual scraping procedures for Phase 1
* Roles and responsibilities for all team members
* Data structure and standardization requirements
* AI agent build process (Phases 1–4)
* Data quality standards and best practices
* Scaling guidelines for Florida-wide expansion

## 9.2 How to Use This Document

* **New team members:** Read Sections 9–13 before starting any work. These cover your immediate responsibilities.
* **Data engineers:** Sections 10, 13, and 14 are your primary reference for schema, pipeline design, and AI build plan.
* **Web scrapers:** Section 11 is your step-by-step operating guide. Follow it for every source you work on.
* **AI builders:** Sections 14 and 16 contain the agent architecture and scaling guidelines.
* **Project lead:** Section 15 (data quality) and Section 16 (scaling) are your review and planning references.

# Section 10 — Incentive Data Pipeline — Full Workflow

## 10.1 End-to-End Pipeline Overview

| **Stage** | **Name** | **Input** | **Output** | **Owner** |
| --- | --- | --- | --- | --- |
| Stage 1 | Source Discovery | Known source list + agent search results | Curated source list with URLs, priority, and scraping method | Scraper + AI Builder |
| Stage 2 | Data Extraction | Source URLs | Raw HTML, text, or PDF content per program | Scraper |
| Stage 3 | LLM Parsing | Raw extracted content | Structured JSON matching incentive\_programs schema | AI Builder |
| Stage 4 | Validation | Structured JSON records | Validated records + flagged exceptions in review queue | Data Engineer |
| Stage 5 | Human Review | Flagged records from validation layer | Corrected and approved records ready for DB load | Data Engineer + Lead |
| Stage 6 | Database Load | Validated + approved records | Active records in PostgreSQL incentive\_programs table | Data Engineer |
| Stage 7 | API Serving | PostgreSQL + Redis cache | Incentive data served to dreamlineai.org in < 2 seconds | Data Engineer |
| Stage 8 | Monitoring & Refresh | Scheduled jobs + change alerts | Up-to-date records, alerts on changes, expiry notifications | All |

## 10.2 Data Flow — Source to User

1. Team identifies incentive source (government site, utility, database)
2. Source is added to the source registry with URL, priority level, and scraping method
3. Scraper visits source and extracts raw content (HTML text, PDF, API response)
4. LLM parser processes raw content and outputs structured JSON
5. Validation layer runs schema checks and flags incomplete or anomalous records
6. Flagged records enter human review queue; clean records go directly to database load
7. Human reviewers correct or approve flagged records
8. All validated records loaded to PostgreSQL incentive\_programs table
9. Redis cache pre-computes incentive lists for every Tampa Bay ZIP code
10. API serves cached results to dreamlineai.org in < 2 seconds when user enters address
11. Scheduler re-runs steps 2–9 on a source-specific refresh cadence (weekly for most, monthly for stable programs)
12. Change detection compares new extraction to stored record and alerts team if values differ

**Section 11 — Manual Scraping Process — Step by Step**

| This section is the daily operating guide for web scrapers during Phase 1.  Follow every step for every source. Do not skip validation or documentation steps.  The notes you write today become the training data for the AI agent tomorrow. |
| --- |

## 11.1 Before You Start Scraping a New Source

1. **Check robots.txt:** Go to [source-domain]/robots.txt. Note any disallowed paths. If the scraping target URL is disallowed, flag it for team review before proceeding.
2. **Check for an API:** Search '[site name] API' and '[site name] data download'. If an API or bulk CSV exists, use that instead of scraping.
3. **Read the Terms of Service:** Scan for restrictions on automated access, commercial use, or data redistribution. Flag any concerns.
4. **Document the source:** Add to the Source Registry: URL, program administrator, data format (HTML/PDF/API), scraping method, priority level, and refresh cadence.

## 11.2 Extracting Incentive Data — Field by Field

1. **Program Name:** Use the official name exactly as written on the source. Do not paraphrase.
2. **Category and Type:** Map to our controlled vocabulary — category: solar/hvac/roof/window/insulation/general\_energy/hurricane/downpayment. Type: tax\_credit/grant/rebate/loan/financing/exemption.
3. **Amount:** Record the exact amount and type. If it is a percentage, record as percentage. If it has a cap, record both. If ambiguous, quote the source text in eligibility\_notes.
4. **Eligibility:** List every eligibility requirement found — ownership required, income limits, property age, property type, geographic scope. If anything is unclear, note it.
5. **Application URL:** Find and test the direct application link. If the program requires contacting an office, record the phone number or email in eligibility\_notes.
6. **Expiry:** Note any stated deadline. If no deadline is found, leave blank — do not assume it is permanent.
7. **Source URL:** Copy the exact URL of the page where you found the data. This is the audit trail.
8. **Last Verified:** Enter today's date.

## 11.3 Quality Checks Before Submitting Any Record

* All required fields are populated — no blank cells in required columns
* Amount has been cross-referenced against a second source (e.g., DSIRE confirms IRS amount)
* Application URL has been tested — link opens and loads the correct page
* Eligibility criteria are specific — not just 'homeowners may apply' but full conditions
* Program is confirmed currently active — not from a 2019 news article about a program that has since ended
* ZIP code scope is correct — state-wide programs marked state-wide, not with a specific ZIP list

## 11.4 Documenting Scraping Challenges

For every source you scrape, write a brief scraping note in the Source Registry:

* What worked well (fast API, clean table structure)
* What was difficult (JavaScript rendering required, PDF extraction, ambiguous eligibility language)
* What is likely to change (amounts updated annually, program closes when funds exhausted)
* Recommended automation approach (Playwright spider, DSIRE API sync, manual monitor only)

| These scraping notes are not optional. They are the design specification for the AI agent.  Every challenge documented in Phase 1 becomes a feature requirement in Phase 2 and 3. |
| --- |

# Section 12 — Roles & Responsibilities

| **Role** | **Phase 1 Responsibilities** | **Phase 2 Responsibilities** | **Success Metric** |
| --- | --- | --- | --- |
| Data Engineer (Lead) | Design and maintain database schema. Integrate DSIRE + Rewiring America APIs. Build validation layer. Own data pipeline architecture. | Build Celery scheduler. Maintain diff engine. Own pipeline reliability. Performance optimization. | Schema deployed Week 1. 95%+ uptime for data pipeline. < 2s API response time. |
| Data Engineer (Support) | Execute bulk HCPA property data load. Build ZIP-to-incentive lookup endpoint. Set up PostgreSQL + Redis infrastructure. | Build monitoring dashboard. Implement change detection alerting. Property data nightly delta. | All Hillsborough parcels loaded by Week 2. Address lookup working by Week 3. |
| Web Scraper | Manual scraping of all P0 and P1 priority sources. Populate standardized template. Document scraping challenges per source. | Build automated Scrapy spiders for top sources. Maintain source registry. QA automated extractions. | 150+ validated records by end of Week 4. Source registry complete. All sources documented. |
| AI Agent Builder | Research LLM parsing approach. Build extraction prompt template. Prototype parser on 10 real pages. Design agent architecture. | Build LLM parser pipeline. Implement structured output. Build confidence scoring. Prototype source discovery agent. | Parser working on 90%+ of test pages. Architecture document approved. Phase 3 plan drafted. |
| Project / Product Lead | Prioritize source list. QA final records for accuracy. Gather contractor + homeowner feedback on which programs matter most. | Define expansion criteria. Review Phase 3 architecture. Manage partner relationships (TECO, PACE providers). | Source priority approved by Day 1. 20 records QA'd per week. Partner conversations started. |

# Section 13 — Data Structure & Standardization Guidelines

## 13.1 Controlled Vocabulary — Use Only These Values

### Category (eligible values)

solar · hvac · roof · windows · insulation · ev\_charger · battery · water\_heater · hurricane · downpayment · weatherization · general\_energy · other

### Type (eligible values)

tax\_credit · grant · rebate · loan · financing · exemption · subsidy

### Level (eligible values)

federal · state · county · city · utility

### Amount Type (eligible values)

fixed\_dollar · percentage · per\_unit · up\_to · tiered

### Property Type (eligible values)

sfh · condo · townhouse · multifamily · commercial · all

## 13.2 Amount Formatting Standards

* **Percentages:** Store as decimal number. 30% → amount\_value = 30, amount\_type = 'percentage'
* **Fixed dollar:** Store as integer. $10,000 → amount\_value = 10000, amount\_type = 'fixed\_dollar'
* **Up-to amounts:** amount\_type = 'up\_to', amount\_value = maximum amount. Example: 'up to $1,200' → amount\_value = 1200
* **Per-unit amounts:** amount\_type = 'per\_unit', amount\_value = per-unit rate. Note unit in eligibility\_notes.
* **Tiered amounts:** Use amount\_type = 'tiered', store tier details as JSON in eligibility\_notes.
* **Ranges:** If a program offers '$75–$200', use amount\_value = 75 (minimum), amount\_max = 200.

## 13.3 ZIP Code Handling

* **Statewide programs:** Leave zip\_codes as NULL — do not fill with every Florida ZIP.
* **County-wide programs:** Leave zip\_codes as NULL but populate county = 'Hillsborough'.
* **Utility programs:** Set utility\_provider field instead of listing ZIP codes. Utility territory drives eligibility.
* **City-specific programs:** Set city = 'Tampa' and county = 'Hillsborough'. Leave zip\_codes NULL unless program has explicit ZIP restrictions.

## 13.4 Date Formatting

* **All dates:** ISO 8601 format — YYYY-MM-DD. Example: 2026-04-15
* **Year-end deadlines:** If program says 'through 2032', record expires\_at = '2032-12-31'
* **Unknown expiry:** Leave expires\_at as NULL. Never assume a program is permanent.
* **last\_verified\_at:** Always update to today's date when a record is reviewed, even if no changes.

# Section 14 — AI Agent Build Process — Detailed Steps

## 14.1 Phase 1 Tasks — Assisted Scraping (Weeks 1–4)

1. **Set up project repository:** GitHub repo with folders: /scrapers, /parsers, /validators, /database, /api, /agents, /docs
2. **Deploy PostgreSQL:** Set up database with incentive\_programs and property\_parcels tables (full schema in engineering spec document)
3. **Integrate DSIRE API:** Register for API key at dsireusa.org/api. Build Python client. Pull all FL programs. Map to our schema. Load to DB.
4. **Integrate Rewiring America API:** Register at api.rewiringamerica.org. Test with Tampa ZIP codes. Integrate into assessment results flow.
5. **Build manual scraping template:** Google Sheet with all required fields as column headers. Dropdown validation for controlled vocabulary fields.
6. **Execute manual scraping:** Scraping team works through P0 and P1 sources. Target 150+ validated records by Week 4 end.
7. **Build ZIP lookup API:** FastAPI endpoint: GET /api/incentives?zip=XXXXX. Returns all programs matching that ZIP.

## 14.2 Phase 2 Tasks — Semi-Automated Pipelines (Weeks 5–10)

1. **Build Scrapy spiders:** One spider per source for top 10 sources. Each spider outputs raw content to a queue.
2. **Build Playwright scrapers:** For JavaScript-heavy sites — Florida Housing, utility portals. Run in headless mode on schedule.
3. **Build LLM parser:** Python function that takes raw HTML/text + source metadata, calls Claude/GPT-4o with extraction prompt, returns structured JSON. Use function calling for structured output.
4. **Build Pydantic validator:** Schema that validates every LLM output. Rejects records missing required fields or with anomalous amounts.
5. **Build human review queue:** Airtable or simple web UI showing flagged records. Reviewer can approve, correct, or reject each record.
6. **Build diff engine:** Compare new scrape results to stored DB record field by field. If any field changes, create alert and log the change.
7. **Set up Celery scheduler:** Weekly jobs for all active scrapers. Monthly deep refresh for stable programs. Daily delta for HCPA property data.

## 14.3 LLM Extraction Prompt Template

| SYSTEM PROMPT:  You are a structured data extraction specialist. Extract incentive program details from the  provided content and return a JSON object matching the schema exactly. Only extract information  explicitly stated in the content. If a field is not mentioned, return null for that field.  Never infer or assume values. Do not hallucinate amounts or eligibility criteria.  USER PROMPT:  Extract all incentive program details from the following content scraped from [SOURCE\_URL].  Content type: [html\_text / pdf\_text / api\_response]  Source name: [DSIRE / TECO / Florida Housing / etc.]  Return a JSON array where each element matches this schema:  { program\_name, category, type, level, amount\_type, amount\_value, amount\_max,  eligible\_property\_types[], eligible\_project\_types[], requires\_homeownership,  income\_required, income\_limit\_pct\_ami, eligibility\_notes, application\_url,  program\_administrator, expires\_at, confidence\_score (0.0–1.0) }  CONTENT TO EXTRACT FROM:  [EXTRACTED\_CONTENT] |
| --- |

## 14.4 Phase 3 Tasks — Intelligent Agents (Weeks 11–18)

1. **Source Discovery Agent:** LangChain / LlamaIndex agent with web search tool. Given a query like 'Florida home renovation incentives 2026', agent finds and evaluates new sources, adds relevant ones to the source registry.
2. **Adaptive Extraction Agent:** Agent that analyzes a URL, determines the best extraction method (API / static scraper / Playwright / PDF), executes it, and handles errors by trying alternatives.
3. **Cross-Reference Validator Agent:** After extracting a program, agent searches for the same program on a secondary source to verify amount and eligibility. Flags discrepancies for human review.
4. **Change Monitor Agent:** Continuously monitors all active programs. When funding exhaustion, deadline, or amount change is detected, generates a human-readable summary of what changed and why it matters.
5. **Feedback Learning Loop:** Human corrections to the review queue are stored as labeled examples. Fine-tune or few-shot prompt the LLM parser with these examples to improve accuracy over time.

# Section 15 — Data Quality Best Practices

## 15.1 The Three Quality Rules

| **Rule** | **What It Means** | **How to Enforce** |
| --- | --- | --- |
| Source of Truth | Every field value must be traceable to a specific URL or document. No values from memory, assumption, or inference. | source\_url required on every record. Validation rejects records without it. |
| Current Over Complete | A record with fewer fields but verified today is better than a complete record that has not been checked in 6 months. | last\_verified\_at required. Records > 90 days old flagged for re-verification. |
| Conservative On Amounts | When in doubt about an amount, use the lower value or record a range. Overpromising an incentive that does not apply destroys user trust. | Amount cross-reference required for all records > $1,000. LLM confidence score tracked. |

## 15.2 Weekly Data Quality Checklist

* Run automated test: query 10 random Tampa ZIP codes — verify result count > 5 programs each
* Check that no records have last\_verified\_at > 90 days — re-verify or mark inactive
* Check for records with expires\_at in the next 30 days — verify program still active
* Review human review queue — zero backlog target at start of each week
* Spot-check 5 random records against their source URL — verify amounts and links still work
* Review any change alerts from the diff engine — update records as needed

## 15.3 Handling Stale or Expired Data

* **Expired programs:** Do NOT delete — set active = false. Retain for audit trail and historical analysis.
* **Programs with unknown expiry:** Re-verify monthly. Set a calendar reminder per source.
* **Programs that go 'paused' (funded out):** Set active = false with notes in eligibility\_notes: 'Program paused — funding exhausted as of [date]. Check [URL] for reopening.'
* **Amount changes:** Update amount\_value, log old value in change history, set last\_verified\_at to today.
* **Application URL changes:** Update URL, test new link, log old URL in scrape\_logs for reference.

# Section 16 — Scaling from Tampa to All of Florida

## 16.1 Phased Geographic Expansion

| **Phase** | **Geography** | **ZIP Codes** | **New Sources to Add** | **Trigger** |
| --- | --- | --- | --- | --- |
| Phase 1 | Tampa City + Hillsborough County | ~40 ZIPs | TECO, Duke, Hillsborough SHIP, Tampa programs | Now — this document |
| Phase 2 | Full Tampa Bay MSA | ~200 ZIPs | Pinellas County programs, St. Pete programs, Pasco SHIP | After Phase 1 QA passes |
| Phase 3 | Central Florida (Orlando MSA) | ~300 ZIPs | Orlando Utilities (OUC), Orange County programs | After AI pipeline is stable |
| Phase 4 | South Florida (Miami / Broward / Palm Beach) | ~400 ZIPs | FPL programs, Miami-Dade programs, SFWMD programs | After Phase 3 launch |
| Phase 5 | All Florida ZIP codes | ~1,000 ZIPs | All remaining utility + county programs statewide | Full AI automation operational |

## 16.2 What Changes With Each New Region

* **Utility provider:** Every region has different utilities. Add utility\_provider to the source registry for each new region before scraping.
* **County-level programs:** Each county has its own SHIP, CDBG, and housing rehabilitation programs. These require fresh research for each county.
* **City-specific programs:** Major cities (Orlando, Jacksonville, Miami) have their own community development programs. Research each city government separately.
* **AMI thresholds:** HUD publishes AMI limits per metro area. Update AMI thresholds when expanding to a new metro.
* **PACE territory:** Confirm which PACE providers are active in the new county. Not all Florida counties have all PACE providers.

## 16.3 State-Level Programs That Apply Everywhere

These programs are statewide and do not require new research for each region — they are already in the database from Phase 1 and apply to all Florida ZIP codes:

* Federal ITC (30% solar tax credit) — applies nationwide
* Federal Energy Efficient Home Improvement Credit (25C) — applies nationwide
* Florida property tax exemption for solar (Statute 196.175) — statewide
* Florida sales tax exemption on solar equipment — statewide
* My Safe Florida Home program — statewide
* Florida Housing Finance Corporation programs (SHIP, HOME, DPA) — statewide
* FEMA hazard mitigation programs — statewide post-disaster
* PACE financing programs (Ygrene, RenewPACE, FRED) — available in most FL counties

## 16.4 Scaling Readiness Checklist — Before Expanding to a New Region

* Phase 1 data quality validated — spot-check pass rate > 95%
* Automated pipeline stable — < 5% human review queue backlog
* HCPA equivalent property data source identified for new county
* Utility provider(s) for new region identified and added to source registry
* County-specific programs researched and added to scraping queue
* City-specific programs researched for any major cities in new region
* AMI thresholds updated for new metro area
* PACE provider coverage confirmed for new county
* API load tested for new ZIP code volume
* QA team has capacity to validate new region's records before go-live

| **End of Document**  *Dreamline AI — Incentive Data Pipeline Kickoff Briefing & SOP v1.0*  dreamlineai.org | Community Dream Foundation | April 2026 |
| --- |