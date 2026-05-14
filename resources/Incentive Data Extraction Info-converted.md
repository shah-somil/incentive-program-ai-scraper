Incentive Data Extraction

Please reach out to me ( @Anirudh (PDT) ) for any clarification, at any stage.

Task:

Extract incentive programs for the columns (i.e., fields) mentioned below and upload them as
“your_name_extracted_tampa_incentives.csv” in the folder “Extracted_Tampa_Incentives".

Columns needed:

program_name, state, city, incentive_type, property_type, description, eligibility_criteria, incentive_amount,
valid_until, updated_at, review_needed, program_links

(Please maintain the same column order)

Field Name

program_name

state

city

incentive_type

property_type

description

eligibility_criteria

incentive_amount

valid_until

updated_at

Meaning/Requirement

Title of the (main) incentive program

State(s) in which the program is valid

City/cities in which the program is valid

One of the 5 incentive types mentioned below

Use what the program information contains but do not
be vague like "Neither" or "Other".

Short description extracted/summarized

Use what the program information contains

Use what the program information contains.

Date of program expiration

Date when latest information about the program was

review_needed

updated

If you feel like any field is missing/ambiguous, include
the program and its corresponding available fields but
mark the review_needed field as “Yes”.

Else, "No"

program_links

URL for the (main) incentive program

Types of Incentives:

Incentive Type

What It Means

Who Offers It

Grants

Rebates

Finance Solutions

Tax Credits

Investments

Money given up front that you
don’t repay

Federal and state agencies, local
governments, green banks,
foundations

Cash returned after you buy or
install something

Utilities, state energy offices, local
governments

Programs that help you pay over
time with easier or cheaper
financing

Banks, credit unions, utilities, state
programs, green banks

Lower the amount of taxes you
owe when you install clean-energy
upgrades

Federal government, state
governments

Large-scale funding for big
clean-energy projects

Government agencies, public
financing authorities, green banks,
development banks, foundations,
institutional investors

Data Sources (Non-Exhaustive):

Only extract active programs (even if the current application window is closed).

A. Government Sources (High Priority)

Federal:

●

●

U.S. Department of Energy

Internal Revenue Service

State:

● Florida energy & housing departments

Local:

●

●

Tampa city programs

Hillsborough County housing & sustainability portals

B. Public Datasets

● U.S. Census Bureau: demographics, income eligibility

● Property appraiser data (Hillsborough County)

● Open data portals

C. Utility & Private Databases

● Utility rebate programs (TECO, etc.)

● Pre-built incentive databases (3rd party APIs/tools)

● Manufacturer rebate programs

Geographic Focus:

●

●

Primary: Tampa City limits + Hillsborough County ZIP codes

Expandable: All of Tampa Bay MSA (Pasco, Pinellas, Manatee, Hernando)

Resources:

●

●

●

●

Example Dataset:   incentives_repo_v3.csv
Web scraping basics:   Data Extraction with Python.docx
Example web scraping code:   scrape_dsire.py
Prompt Engineering Best Practices:   Prompt Engineering Best Practices.pdf

