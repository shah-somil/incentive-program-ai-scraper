"""Curated baseline records.

These are programs the briefing documents call out explicitly (federal IRA
credits, statewide Florida tax exemptions, PACE administrators, etc.) where
the program details are stable enough to encode directly.

They serve two purposes:

1. Guarantee a non-empty, useful CSV even if every live source is unreachable.
2. Provide a known-good baseline that the live scrapers can deduplicate
   against.

Sources are documented per-record in the ``source_url`` field; the data was
last verified against public IRS / Florida DOR / utility / DSIRE pages on
2026-05-04.
"""

from __future__ import annotations

from typing import List

from ..schema import AmountType, Level, RawIncentive, RawType, today_iso


def _today() -> str:
    return today_iso()


def _default_ongoing(records: List[RawIncentive]) -> List[RawIncentive]:
    """Apply curated-baseline defaults to a batch of records.

    Stamps ``expires_at = "Ongoing"`` for evergreen programs and tags every
    record with ``extraction_source = "curated"`` so the provenance survives
    through the pipeline.
    """

    out: List[RawIncentive] = []
    for r in records:
        updates = {"extraction_source": "curated"}
        if not r.expires_at:
            updates["expires_at"] = "Ongoing"
        out.append(r.model_copy(update=updates))
    return out


def federal_baseline() -> List[RawIncentive]:
    today = _today()
    return _default_ongoing([
        RawIncentive(
            program_name="Residential Clean Energy Credit (Section 25D)",
            level=Level.federal,
            type=RawType.tax_credit,
            amount_type=AmountType.percentage,
            amount_value=30,
            amount_text="30% of qualified clean-energy expenditures (no cap for solar / battery / geothermal / fuel cells; battery storage 3+ kWh).",
            eligible_property_types=["sfh", "condo", "townhouse"],
            eligible_project_types=[
                "solar_pv", "solar_water_heating", "small_wind",
                "geothermal_heat_pump", "battery_storage", "fuel_cell",
            ],
            requires_homeownership=True,
            income_required=False,
            description=(
                "Federal income tax credit equal to 30% of the cost of new, qualified clean-energy "
                "property installed at a U.S. residence. Phases down to 26% in 2033 and 22% in 2034."
            ),
            eligibility_notes=(
                "Property must be located in the U.S. and used as a residence by the taxpayer. "
                "Claim with IRS Form 5695. No income limit. Credit is non-refundable but unused "
                "amounts may be carried forward."
            ),
            program_administrator="Internal Revenue Service",
            application_url="https://www.irs.gov/credits-deductions/residential-clean-energy-credit",
            source_url="https://www.irs.gov/credits-deductions/residential-clean-energy-credit",
            expires_at="2034-12-31",
            last_verified_at=today,
            confidence_score=0.95,
        ),
        RawIncentive(
            program_name="Energy Efficient Home Improvement Credit (Section 25C)",
            level=Level.federal,
            type=RawType.tax_credit,
            amount_type=AmountType.percentage,
            amount_value=30,
            amount_max=3200,
            amount_text="30% of qualified efficiency upgrade costs, capped at $1,200/yr for envelope items + $2,000/yr for heat pumps and biomass stoves.",
            eligible_property_types=["sfh", "condo", "townhouse"],
            eligible_project_types=[
                "insulation", "windows", "doors", "air_sealing",
                "heat_pump", "heat_pump_water_heater", "biomass_stove",
                "central_ac", "furnace", "boiler", "home_energy_audit",
            ],
            requires_homeownership=True,
            income_required=False,
            description=(
                "Federal income tax credit for qualifying energy-efficiency upgrades to an existing "
                "primary residence. Includes specific sub-caps such as $600 for windows, $500 for "
                "doors, $150 for home energy audits, and $2,000 combined for heat pumps."
            ),
            eligibility_notes=(
                "Must be installed in the taxpayer's primary residence in the United States. "
                "Claim with IRS Form 5695. Equipment must meet the IRS efficiency thresholds in "
                "place at the time of installation."
            ),
            program_administrator="Internal Revenue Service",
            application_url="https://www.irs.gov/credits-deductions/energy-efficient-home-improvement-credit",
            source_url="https://www.irs.gov/credits-deductions/energy-efficient-home-improvement-credit",
            expires_at="2032-12-31",
            last_verified_at=today,
            confidence_score=0.95,
        ),
        RawIncentive(
            program_name="HOMES Rebate Program (DOE Section 50121)",
            level=Level.federal,
            type=RawType.rebate,
            amount_type=AmountType.up_to,
            amount_value=8000,
            amount_text="Up to $8,000 per project for whole-home energy retrofits; doubled for low/moderate-income households.",
            eligible_property_types=["sfh", "condo", "townhouse", "multifamily"],
            eligible_project_types=["whole_home_retrofit", "energy_efficiency"],
            income_required=True,
            requires_homeownership=False,
            description=(
                "Inflation Reduction Act rebate for whole-home energy retrofits, scaled by modeled or "
                "measured energy savings. Administered by states; Florida DEO is the designated "
                "implementer."
            ),
            eligibility_notes=(
                "Rebate amount depends on household income (above/below 80% AMI) and projected "
                "energy savings (20% / 35% thresholds). Only available once Florida launches its "
                "implementation; check the Florida program portal for live status."
            ),
            program_administrator="U.S. Department of Energy / Florida Department of Commerce",
            application_url="https://www.energy.gov/scep/home-energy-rebates",
            source_url="https://www.energy.gov/scep/home-energy-rebates",
            expires_at="2031-09-30",
            last_verified_at=today,
            confidence_score=0.85,
        ),
        RawIncentive(
            program_name="High-Efficiency Electric Home Rebate Act (HEEHRA)",
            level=Level.federal,
            type=RawType.rebate,
            amount_type=AmountType.up_to,
            amount_value=14000,
            amount_text="Up to $14,000 per household for electrification (heat pumps, induction stoves, electrical panels, wiring) for income-qualified households.",
            eligible_property_types=["sfh", "condo", "townhouse", "multifamily"],
            eligible_project_types=[
                "heat_pump", "heat_pump_water_heater", "induction_stove",
                "heat_pump_dryer", "electrical_panel_upgrade", "wiring",
                "insulation", "ventilation",
            ],
            income_required=True,
            income_limit_pct_ami=150,
            requires_homeownership=False,
            description=(
                "IRA point-of-sale rebate program for electrification upgrades for households below "
                "150% of Area Median Income. Up to 100% of cost covered for households below 80% AMI."
            ),
            eligibility_notes=(
                "Households at or below 80% AMI: up to 100% of project cost. 80%-150% AMI: up to 50%. "
                "Per-item caps include $8,000 for heat pumps and $1,750 for heat pump water heaters."
            ),
            program_administrator="U.S. Department of Energy / Florida Department of Commerce",
            application_url="https://www.energy.gov/scep/home-energy-rebates",
            source_url="https://www.energy.gov/scep/home-energy-rebates",
            expires_at="2031-09-30",
            last_verified_at=today,
            confidence_score=0.85,
        ),
        RawIncentive(
            program_name="FEMA Hazard Mitigation Grant Program (HMGP)",
            level=Level.federal,
            type=RawType.grant,
            amount_type=AmountType.percentage,
            amount_value=75,
            amount_text="Up to 75% federal cost share for eligible mitigation projects (homeowners apply through their state/local government).",
            eligible_property_types=["sfh", "condo", "townhouse", "multifamily"],
            eligible_project_types=[
                "wind_retrofit", "elevation", "flood_mitigation",
                "tornado_safe_room", "wildfire_mitigation",
            ],
            income_required=False,
            requires_homeownership=True,
            description=(
                "Post-disaster mitigation grant administered by FEMA through state and local "
                "governments. Funds projects that reduce future disaster losses, including wind "
                "retrofits, elevation, and flood mitigation for homes."
            ),
            eligibility_notes=(
                "Available only after a Presidential disaster declaration. Florida Division of "
                "Emergency Management coordinates eligible projects; homeowners typically apply via "
                "their county emergency management office."
            ),
            program_administrator="Federal Emergency Management Agency / Florida Division of Emergency Management",
            application_url="https://www.fema.gov/grants/mitigation/hazard-mitigation",
            source_url="https://www.fema.gov/grants/mitigation/hazard-mitigation",
            expires_at="Ongoing",
            last_verified_at=today,
            confidence_score=0.8,
        ),
        RawIncentive(
            program_name="FEMA Building Resilient Infrastructure and Communities (BRIC)",
            level=Level.federal,
            type=RawType.investment,
            amount_type=AmountType.up_to,
            amount_value=50000000,
            amount_text="Competitive grants up to $50M per project for state, local, tribal, and territorial governments.",
            eligible_property_types=["all"],
            eligible_project_types=[
                "infrastructure_resilience", "flood_mitigation", "wind_mitigation",
            ],
            income_required=False,
            requires_homeownership=False,
            description=(
                "Competitive pre-disaster mitigation grant program. Funds projects that reduce risk "
                "from natural hazards, with capability- and capacity-building set-asides."
            ),
            eligibility_notes=(
                "Eligible applicants are state, local, tribal, and territorial governments. "
                "Individuals cannot apply directly but benefit from sub-applications such as wind "
                "retrofit programs administered locally."
            ),
            program_administrator="Federal Emergency Management Agency",
            application_url="https://www.fema.gov/grants/mitigation/building-resilient-infrastructure-communities",
            source_url="https://www.fema.gov/grants/mitigation/building-resilient-infrastructure-communities",
            expires_at="Ongoing",
            last_verified_at=today,
            confidence_score=0.78,
        ),
    ])


def state_baseline() -> List[RawIncentive]:
    today = _today()
    return _default_ongoing([
        RawIncentive(
            program_name="Florida Property Tax Exemption for Solar / Renewable Energy (Statute 196.175)",
            level=Level.state,
            type=RawType.exemption,
            amount_type=AmountType.percentage,
            amount_value=100,
            amount_text="100% of the assessed value attributable to a renewable energy source device is exempt from ad valorem property taxation.",
            eligible_property_types=["sfh", "condo", "townhouse", "multifamily", "commercial"],
            eligible_project_types=["solar_pv", "solar_water_heating", "wind", "geothermal", "biomass"],
            requires_homeownership=True,
            income_required=False,
            description=(
                "Renewable energy source devices installed on real property are exempt from being "
                "considered when determining the assessed value for property taxes."
            ),
            eligibility_notes=(
                "Applies to renewable energy source devices installed on or after January 1, 2013, "
                "for residential property and on or after January 1, 2018, for non-residential. "
                "Filed with the local property appraiser."
            ),
            program_administrator="Florida Department of Revenue",
            application_url="https://floridarevenue.com/property/Pages/Taxpayers_Exemptions.aspx",
            source_url="https://floridarevenue.com/property/Pages/Taxpayers_Exemptions.aspx",
            last_verified_at=today,
            confidence_score=0.92,
        ),
        RawIncentive(
            program_name="Florida Sales Tax Exemption on Solar Energy Systems (Statute 212.08(7)(hh))",
            level=Level.state,
            type=RawType.exemption,
            amount_type=AmountType.percentage,
            amount_value=100,
            amount_text="6% Florida sales tax fully waived on solar energy systems and components.",
            eligible_property_types=["sfh", "condo", "townhouse", "multifamily", "commercial"],
            eligible_project_types=["solar_pv", "solar_water_heating"],
            requires_homeownership=False,
            income_required=False,
            description=(
                "Sales of solar energy systems and components are exempt from Florida sales and use tax."
            ),
            eligibility_notes=(
                "Applies to equipment certified by the Florida Solar Energy Center (FSEC). Buyer "
                "submits exemption certificate to seller."
            ),
            program_administrator="Florida Department of Revenue",
            application_url="https://floridarevenue.com/taxes/taxesfees/Pages/sales_tax.aspx",
            source_url="https://floridarevenue.com/taxes/taxesfees/Pages/sales_tax.aspx",
            last_verified_at=today,
            confidence_score=0.92,
        ),
        RawIncentive(
            program_name="My Safe Florida Home Hurricane Mitigation Grant",
            level=Level.state,
            type=RawType.grant,
            amount_type=AmountType.up_to,
            amount_value=10000,
            amount_text="Up to $10,000 grant on a $2-for-$1 match for approved hurricane mitigation improvements.",
            eligible_property_types=["sfh"],
            eligible_project_types=[
                "roof_strengthening", "opening_protection", "impact_windows",
                "impact_doors", "secondary_water_resistance",
            ],
            requires_homeownership=True,
            income_required=False,
            description=(
                "State-funded hurricane mitigation grant for owner-occupied single-family homes in "
                "Florida. Provides a free wind mitigation inspection and a matching grant for "
                "approved improvements."
            ),
            eligibility_notes=(
                "Home must be insured for less than $700,000, located in Florida, and be the "
                "homeowner's primary residence. Application windows open periodically; check "
                "mysafeflhome.com for the current opening."
            ),
            program_administrator="Florida Department of Financial Services",
            application_url="https://mysafeflhome.com/",
            source_url="https://mysafeflhome.com/",
            last_verified_at=today,
            confidence_score=0.88,
        ),
        RawIncentive(
            program_name="Florida State Housing Initiatives Partnership (SHIP) Program",
            level=Level.state,
            type=RawType.grant,
            amount_type=AmountType.up_to,
            amount_value=75000,
            amount_text="Down-payment, rehab, and disaster-recovery assistance varies by local SHIP plan; commonly up to $40,000-$75,000 per household.",
            eligible_property_types=["sfh", "condo", "townhouse"],
            eligible_project_types=["down_payment", "rehab", "disaster_recovery", "weatherization"],
            requires_homeownership=True,
            income_required=True,
            income_limit_pct_ami=140,
            description=(
                "Florida-funded program distributing housing dollars to all 67 counties and entitlement "
                "cities. Each jurisdiction adopts a local housing assistance plan (LHAP) defining "
                "eligible activities and award limits."
            ),
            eligibility_notes=(
                "Income-qualified households (very low / low / moderate, up to 140% AMI). Specific "
                "uses (down payment, owner-occupied rehab, disaster recovery, etc.) and award caps "
                "set by each county's LHAP."
            ),
            program_administrator="Florida Housing Finance Corporation",
            application_url="https://www.floridahousing.org/programs/special-programs/ship---state-housing-initiatives-partnership-program",
            source_url="https://www.floridahousing.org/programs/special-programs/ship---state-housing-initiatives-partnership-program",
            last_verified_at=today,
            confidence_score=0.86,
        ),
        RawIncentive(
            program_name="Florida Hometown Heroes Housing Program",
            level=Level.state,
            type=RawType.loan,
            amount_type=AmountType.up_to,
            amount_value=35000,
            amount_text="Up to 5% of the first mortgage (max $35,000) as 0%, deferred, non-amortizing second mortgage for down payment and closing costs.",
            eligible_property_types=["sfh", "condo", "townhouse"],
            eligible_project_types=["down_payment", "closing_costs"],
            requires_homeownership=True,
            income_required=True,
            income_limit_pct_ami=150,
            description=(
                "Down-payment and closing-cost assistance for income-qualified Florida workforce "
                "homebuyers (first-time or repeat) earning up to 150% of the local AMI."
            ),
            eligibility_notes=(
                "Borrower must be employed full-time by a Florida-based employer, occupy the home "
                "as primary residence, and complete approved homebuyer education. Funded as a "
                "second mortgage that is repaid only on sale, refinance, transfer, or no-longer-"
                "primary-residence event."
            ),
            program_administrator="Florida Housing Finance Corporation",
            application_url="https://www.floridahousing.org/programs/homebuyer-overview-page/hometown-heroes",
            source_url="https://www.floridahousing.org/programs/homebuyer-overview-page/hometown-heroes",
            last_verified_at=today,
            confidence_score=0.86,
        ),
        RawIncentive(
            program_name="Florida Assist (FL Assist) Down-Payment Assistance",
            level=Level.state,
            type=RawType.loan,
            amount_type=AmountType.up_to,
            amount_value=10000,
            amount_text="Up to $10,000 deferred 0% second-mortgage for down payment and closing costs.",
            eligible_property_types=["sfh", "condo", "townhouse"],
            eligible_project_types=["down_payment", "closing_costs"],
            requires_homeownership=True,
            income_required=True,
            description=(
                "0%, deferred-payment second mortgage paired with Florida Housing first mortgage "
                "products for income-qualified first-time homebuyers."
            ),
            eligibility_notes=(
                "Used in conjunction with a Florida Housing first mortgage. Repayable on sale, "
                "refinance, transfer, or when the home is no longer the buyer's primary residence."
            ),
            program_administrator="Florida Housing Finance Corporation",
            application_url="https://www.floridahousing.org/programs/homebuyer-overview-page/down-payment-assistance",
            source_url="https://www.floridahousing.org/programs/homebuyer-overview-page/down-payment-assistance",
            last_verified_at=today,
            confidence_score=0.85,
        ),
        RawIncentive(
            program_name="Florida HFA Preferred and HFA Advantage First Mortgage",
            level=Level.state,
            type=RawType.financing,
            amount_text="Below-market 30-year fixed-rate first mortgage paired with up to 5% in down-payment assistance.",
            eligible_property_types=["sfh", "condo", "townhouse"],
            eligible_project_types=["home_purchase"],
            requires_homeownership=True,
            income_required=True,
            description=(
                "Conventional, FHA, VA, and USDA first mortgages offered through participating "
                "lenders, paired with FL Assist or Florida Hometown Heroes down-payment assistance."
            ),
            eligibility_notes=(
                "Income and purchase-price limits vary by county. Borrower must complete a "
                "Florida Housing-approved homebuyer education course."
            ),
            program_administrator="Florida Housing Finance Corporation",
            application_url="https://www.floridahousing.org/programs/homebuyer-overview-page",
            source_url="https://www.floridahousing.org/programs/homebuyer-overview-page",
            last_verified_at=today,
            confidence_score=0.82,
        ),
    ])


def utility_baseline() -> List[RawIncentive]:
    today = _today()
    return _default_ongoing([
        RawIncentive(
            program_name="TECO Energy Planner Heat Pump Rebate",
            level=Level.utility,
            type=RawType.rebate,
            amount_type=AmountType.up_to,
            amount_value=265,
            amount_text="$265 rebate for installing a qualifying high-efficiency electric heat pump.",
            eligible_property_types=["sfh", "condo", "townhouse"],
            eligible_project_types=["heat_pump"],
            requires_homeownership=True,
            income_required=False,
            utility_provider="Tampa Electric (TECO)",
            description=(
                "Tampa Electric residential rebate for replacing electric resistance or older HVAC "
                "with a qualifying high-efficiency heat pump."
            ),
            eligibility_notes=(
                "Customer must be on TECO residential service. System must meet TECO's minimum "
                "SEER/HSPF efficiency thresholds. Rebate paid after installation and inspection."
            ),
            program_administrator="Tampa Electric",
            application_url="https://www.tampaelectric.com/residential/saveenergy/",
            source_url="https://www.tampaelectric.com/residential/saveenergy/",
            last_verified_at=today,
            confidence_score=0.78,
        ),
        RawIncentive(
            program_name="TECO Ceiling Insulation Rebate",
            level=Level.utility,
            type=RawType.rebate,
            amount_type=AmountType.up_to,
            amount_value=200,
            amount_text="Up to $200 for adding ceiling insulation to qualifying levels.",
            eligible_property_types=["sfh", "condo", "townhouse"],
            eligible_project_types=["insulation"],
            requires_homeownership=True,
            income_required=False,
            utility_provider="Tampa Electric (TECO)",
            description=(
                "Rebate for upgrading attic insulation to TECO's qualifying R-value level."
            ),
            eligibility_notes=(
                "Existing insulation must be R-19 or below; upgrade must reach R-30 or higher. "
                "Rebate paid after post-install inspection."
            ),
            program_administrator="Tampa Electric",
            application_url="https://www.tampaelectric.com/residential/saveenergy/",
            source_url="https://www.tampaelectric.com/residential/saveenergy/",
            last_verified_at=today,
            confidence_score=0.74,
        ),
        RawIncentive(
            program_name="TECO Window Solar Screen Rebate",
            level=Level.utility,
            type=RawType.rebate,
            amount_type=AmountType.per_unit,
            amount_value=0.40,
            amount_text="$0.40 per square foot for installing exterior solar screens on qualifying windows.",
            eligible_property_types=["sfh", "condo", "townhouse"],
            eligible_project_types=["solar_screens"],
            requires_homeownership=True,
            income_required=False,
            utility_provider="Tampa Electric (TECO)",
            description=(
                "Per-square-foot rebate for adding exterior solar screens to reduce solar heat gain."
            ),
            eligibility_notes="Exterior screens only; interior films or shades are not eligible.",
            program_administrator="Tampa Electric",
            application_url="https://www.tampaelectric.com/residential/saveenergy/",
            source_url="https://www.tampaelectric.com/residential/saveenergy/",
            last_verified_at=today,
            confidence_score=0.7,
        ),
        RawIncentive(
            program_name="TECO Duct Test and Repair Rebate",
            level=Level.utility,
            type=RawType.rebate,
            amount_type=AmountType.up_to,
            amount_value=125,
            amount_text="Up to $125 rebate for sealing and repairing leaky HVAC ducts.",
            eligible_property_types=["sfh", "condo", "townhouse"],
            eligible_project_types=["duct_sealing"],
            requires_homeownership=True,
            income_required=False,
            utility_provider="Tampa Electric (TECO)",
            description="Rebate for measured duct leakage reduction performed by a participating contractor.",
            eligibility_notes="Leakage reduction must be verified via Duct Blaster test pre/post.",
            program_administrator="Tampa Electric",
            application_url="https://www.tampaelectric.com/residential/saveenergy/",
            source_url="https://www.tampaelectric.com/residential/saveenergy/",
            last_verified_at=today,
            confidence_score=0.7,
        ),
        RawIncentive(
            program_name="TECO Energy Audit (Free)",
            level=Level.utility,
            type=RawType.rebate,
            amount_text="Free in-home or virtual energy audit for residential customers.",
            eligible_property_types=["sfh", "condo", "townhouse"],
            eligible_project_types=["home_energy_audit"],
            requires_homeownership=False,
            income_required=False,
            utility_provider="Tampa Electric (TECO)",
            description="No-cost residential energy audit identifying upgrade opportunities and TECO rebates.",
            eligibility_notes="Limited to TECO residential service customers. Schedule via tampaelectric.com.",
            program_administrator="Tampa Electric",
            application_url="https://www.tampaelectric.com/residential/saveenergy/energyaudit/",
            source_url="https://www.tampaelectric.com/residential/saveenergy/energyaudit/",
            last_verified_at=today,
            confidence_score=0.85,
        ),
        RawIncentive(
            program_name="Duke Energy Florida Smart $aver Heat Pump Rebate",
            level=Level.utility,
            type=RawType.rebate,
            amount_type=AmountType.up_to,
            amount_value=350,
            amount_text="Up to $350 rebate for replacing electric resistance heating with a qualifying heat pump.",
            eligible_property_types=["sfh", "condo", "townhouse"],
            eligible_project_types=["heat_pump"],
            requires_homeownership=True,
            income_required=False,
            utility_provider="Duke Energy Florida",
            description="Rebate for installing a qualifying high-efficiency heat pump on a Duke Energy Florida residential account.",
            eligibility_notes="Customer must be on Duke Energy Florida residential service. System efficiency must meet program minimums.",
            program_administrator="Duke Energy Florida",
            application_url="https://www.duke-energy.com/home/products/save-energy-and-money",
            source_url="https://www.duke-energy.com/home/products/save-energy-and-money",
            last_verified_at=today,
            confidence_score=0.7,
        ),
        RawIncentive(
            program_name="Duke Energy Florida Home Energy Check",
            level=Level.utility,
            type=RawType.rebate,
            amount_text="Free virtual or in-home energy check identifying efficiency upgrades.",
            eligible_property_types=["sfh", "condo", "townhouse"],
            eligible_project_types=["home_energy_audit"],
            requires_homeownership=False,
            income_required=False,
            utility_provider="Duke Energy Florida",
            description="No-cost residential energy check for Duke Energy Florida customers.",
            eligibility_notes="Available to Duke Energy Florida residential service customers.",
            program_administrator="Duke Energy Florida",
            application_url="https://www.duke-energy.com/home/products/home-energy-check",
            source_url="https://www.duke-energy.com/home/products/home-energy-check",
            last_verified_at=today,
            confidence_score=0.85,
        ),
        RawIncentive(
            program_name="Duke Energy Florida Attic Insulation Rebate",
            level=Level.utility,
            type=RawType.rebate,
            amount_type=AmountType.up_to,
            amount_value=200,
            amount_text="Up to $200 rebate for adding attic insulation that meets Duke's R-value upgrade thresholds.",
            eligible_property_types=["sfh", "condo", "townhouse"],
            eligible_project_types=["insulation"],
            requires_homeownership=True,
            income_required=False,
            utility_provider="Duke Energy Florida",
            description="Rebate for upgrading attic insulation in qualifying Duke Energy Florida residences.",
            eligibility_notes="Existing insulation must be at or below R-19; upgrade must reach R-30 or higher.",
            program_administrator="Duke Energy Florida",
            application_url="https://www.duke-energy.com/home/products/save-energy-and-money",
            source_url="https://www.duke-energy.com/home/products/save-energy-and-money",
            last_verified_at=today,
            confidence_score=0.65,
        ),
    ])


def local_baseline() -> List[RawIncentive]:
    today = _today()
    return _default_ongoing([
        RawIncentive(
            program_name="Hillsborough County SHIP Owner-Occupied Rehabilitation",
            level=Level.county,
            type=RawType.grant,
            amount_type=AmountType.up_to,
            amount_value=75000,
            amount_text="Forgivable loan / grant up to $75,000 for code-related rehabilitation of an owner-occupied home.",
            eligible_property_types=["sfh", "condo", "townhouse"],
            eligible_project_types=["rehab", "roof", "hvac", "accessibility", "code_repair"],
            requires_homeownership=True,
            income_required=True,
            income_limit_pct_ami=80,
            county="Hillsborough",
            description=(
                "Hillsborough County uses SHIP funds for owner-occupied rehabilitation, including roof "
                "replacement, HVAC, accessibility modifications, and code-related repairs."
            ),
            eligibility_notes=(
                "Household income must be at or below 80% AMI. Property must be owner-occupied "
                "primary residence in Hillsborough County (excluding Tampa city limits, which run "
                "their own SHIP program)."
            ),
            program_administrator="Hillsborough County Affordable Housing Services",
            application_url="https://hcfl.gov/services/housing/own-a-home/home-repairs",
            source_url="https://hcfl.gov/services/housing/own-a-home/home-repairs",
            last_verified_at=today,
            confidence_score=0.78,
        ),
        RawIncentive(
            program_name="Hillsborough County Down Payment Assistance Program",
            level=Level.county,
            type=RawType.loan,
            amount_type=AmountType.up_to,
            amount_value=40000,
            amount_text="Up to $40,000 in deferred 0% second-mortgage assistance for income-qualified first-time homebuyers.",
            eligible_property_types=["sfh", "condo", "townhouse"],
            eligible_project_types=["down_payment", "closing_costs"],
            requires_homeownership=True,
            income_required=True,
            income_limit_pct_ami=140,
            county="Hillsborough",
            description=(
                "Down-payment and closing-cost assistance for first-time buyers purchasing in "
                "unincorporated Hillsborough County or Plant City / Temple Terrace."
            ),
            eligibility_notes=(
                "First-time homebuyer; must complete approved homebuyer education; assistance "
                "structured as a 0% deferred-payment second mortgage repaid on sale, refinance, "
                "or when no longer primary residence."
            ),
            program_administrator="Hillsborough County Affordable Housing Services",
            application_url="https://hcfl.gov/services/housing/buy-a-home/down-payment-assistance",
            source_url="https://hcfl.gov/services/housing/buy-a-home/down-payment-assistance",
            last_verified_at=today,
            confidence_score=0.76,
        ),
        RawIncentive(
            program_name="City of Tampa Dare to Own the Dream (DDOD)",
            level=Level.city,
            type=RawType.loan,
            amount_type=AmountType.up_to,
            amount_value=14999,
            amount_text="Up to $14,999 in deferred 0% down-payment and closing-cost assistance.",
            eligible_property_types=["sfh", "condo", "townhouse"],
            eligible_project_types=["down_payment", "closing_costs"],
            requires_homeownership=True,
            income_required=True,
            income_limit_pct_ami=120,
            city="Tampa",
            description=(
                "City of Tampa down-payment assistance program for first-time homebuyers purchasing "
                "inside Tampa city limits."
            ),
            eligibility_notes=(
                "Household income up to 120% AMI. Borrower must complete HUD-approved homebuyer "
                "education. Funded as 0% deferred second mortgage repaid on sale, transfer, or refi."
            ),
            program_administrator="City of Tampa Housing & Community Development",
            application_url="https://www.tampa.gov/housing-and-community-development/programs/buying-a-home",
            source_url="https://www.tampa.gov/housing-and-community-development/programs/buying-a-home",
            last_verified_at=today,
            confidence_score=0.74,
        ),
        RawIncentive(
            program_name="City of Tampa Owner-Occupied Rehabilitation",
            level=Level.city,
            type=RawType.grant,
            amount_type=AmountType.up_to,
            amount_value=50000,
            amount_text="Up to $50,000 forgivable rehabilitation loan for income-qualified Tampa homeowners.",
            eligible_property_types=["sfh", "townhouse"],
            eligible_project_types=["rehab", "roof", "hvac", "accessibility", "code_repair"],
            requires_homeownership=True,
            income_required=True,
            income_limit_pct_ami=80,
            city="Tampa",
            description=(
                "City of Tampa owner-occupied rehabilitation program funded with SHIP and CDBG. "
                "Addresses code violations, roof replacement, accessibility, and major systems."
            ),
            eligibility_notes=(
                "Household income at or below 80% AMI. Property must be primary residence in Tampa "
                "city limits. Forgivable over an affordability period set per program guidelines."
            ),
            program_administrator="City of Tampa Housing & Community Development",
            application_url="https://www.tampa.gov/housing-and-community-development/programs/owner-occupied-rehabilitation",
            source_url="https://www.tampa.gov/housing-and-community-development/programs/owner-occupied-rehabilitation",
            last_verified_at=today,
            confidence_score=0.72,
        ),
        RawIncentive(
            program_name="Hillsborough County Weatherization Assistance Program (WAP)",
            level=Level.county,
            type=RawType.grant,
            amount_type=AmountType.up_to,
            amount_value=8000,
            amount_text="Free weatherization services (insulation, air sealing, duct repair, HVAC tune-up) up to ~$8,000 per home.",
            eligible_property_types=["sfh", "condo", "townhouse", "multifamily"],
            eligible_project_types=["weatherization", "insulation", "duct_sealing", "hvac"],
            requires_homeownership=False,
            income_required=True,
            income_limit_pct_ami=80,
            county="Hillsborough",
            description=(
                "Federally-funded weatherization services delivered by Hillsborough County for "
                "income-eligible households. Covers insulation, air sealing, HVAC tune-ups, and "
                "limited mechanical repairs."
            ),
            eligibility_notes=(
                "Household income at or below 200% of the federal poverty level (or otherwise meeting "
                "DOE WAP eligibility). Owners and renters can both qualify, but landlord consent "
                "required for rentals."
            ),
            program_administrator="Hillsborough County Affordable Housing Services / DOE WAP",
            application_url="https://hcfl.gov/services/housing/own-a-home/home-repairs",
            source_url="https://hcfl.gov/services/housing/own-a-home/home-repairs",
            last_verified_at=today,
            confidence_score=0.7,
        ),
        RawIncentive(
            program_name="Florida PACE Funding Agency (Residential PACE)",
            level=Level.state,
            type=RawType.financing,
            amount_type=AmountType.up_to,
            amount_value=500000,
            amount_text="Long-term financing repaid via property tax assessments for qualifying improvements.",
            eligible_property_types=["sfh", "condo", "townhouse", "multifamily", "commercial"],
            eligible_project_types=["solar_pv", "roof", "hvac", "windows", "wind_mitigation", "impact_doors"],
            requires_homeownership=True,
            income_required=False,
            description=(
                "PACE financing for energy efficiency, renewable energy, and wind/hurricane "
                "resilience improvements in participating Florida counties and municipalities."
            ),
            eligibility_notes=(
                "Underwriting based on home equity rather than FICO; repayment through annual "
                "property tax assessment. Available only in counties that have opted in."
            ),
            program_administrator="Florida PACE Funding Agency",
            application_url="https://www.floridapace.gov/",
            source_url="https://www.floridapace.gov/",
            last_verified_at=today,
            confidence_score=0.8,
        ),
        RawIncentive(
            program_name="Ygrene PACE Financing (Florida Residential)",
            level=Level.state,
            type=RawType.financing,
            amount_type=AmountType.up_to,
            amount_value=500000,
            amount_text="Up to 100% financing for energy and hurricane resilience improvements, repaid via property tax bill.",
            eligible_property_types=["sfh", "condo", "townhouse", "multifamily", "commercial"],
            eligible_project_types=["solar_pv", "roof", "hvac", "wind_mitigation", "impact_windows"],
            requires_homeownership=True,
            income_required=False,
            description=(
                "Ygrene-administered PACE program available in Florida counties that have opted in. "
                "Funds qualifying clean-energy and resiliency upgrades with 5-30 year terms."
            ),
            eligibility_notes=(
                "Approval is asset-based (home equity, tax/mortgage current). Confirm county "
                "participation before applying. Adds an annual non-ad-valorem assessment to the "
                "property."
            ),
            program_administrator="Ygrene Energy Fund",
            application_url="https://ygrene.com/",
            source_url="https://ygrene.com/",
            last_verified_at=today,
            confidence_score=0.7,
        ),
        RawIncentive(
            program_name="RenewPACE Residential PACE Financing",
            level=Level.state,
            type=RawType.financing,
            amount_type=AmountType.up_to,
            amount_value=500000,
            amount_text="PACE financing for energy and storm-hardening improvements with terms up to 30 years.",
            eligible_property_types=["sfh", "condo", "townhouse", "multifamily", "commercial"],
            eligible_project_types=["solar_pv", "roof", "hvac", "wind_mitigation", "impact_windows"],
            requires_homeownership=True,
            income_required=False,
            description="RenewPACE-administered PACE financing for participating Florida jurisdictions.",
            eligibility_notes=(
                "Equity-based underwriting; assessment added to annual property tax bill. Verify "
                "county opt-in before scheduling work."
            ),
            program_administrator="RenewPACE",
            application_url="https://renewfinancial.com/",
            source_url="https://renewfinancial.com/",
            last_verified_at=today,
            confidence_score=0.6,
        ),
        RawIncentive(
            program_name="FRED Local PACE (Florida Resiliency & Energy District)",
            level=Level.state,
            type=RawType.financing,
            amount_type=AmountType.up_to,
            amount_value=500000,
            amount_text="PACE financing administered by the Florida Resiliency & Energy District.",
            eligible_property_types=["sfh", "condo", "townhouse", "multifamily", "commercial"],
            eligible_project_types=["solar_pv", "roof", "hvac", "wind_mitigation", "impact_windows"],
            requires_homeownership=True,
            income_required=False,
            description=(
                "FRED is a Florida interlocal agency offering residential and commercial PACE in "
                "participating member counties and cities."
            ),
            eligibility_notes=(
                "County or municipal opt-in required. Equity-based underwriting and tax-bill "
                "repayment."
            ),
            program_administrator="Florida Resiliency & Energy District (FRED)",
            application_url="https://www.fredelocal.com/",
            source_url="https://www.fredelocal.com/",
            last_verified_at=today,
            confidence_score=0.6,
        ),
    ])
