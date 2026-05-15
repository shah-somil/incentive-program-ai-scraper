"""Prompt templates for LLM-based incentive extraction."""

from __future__ import annotations


SYSTEM_PROMPT = (
    "You are a structured data extraction specialist for property-improvement "
    "incentive programs (rebates, tax credits, grants, financing, exemptions). "
    "Extract every distinct program described in the provided page content. "
    "Only use information explicitly stated in the content. If a field is not "
    "mentioned, return null. Never infer amounts, deadlines, or eligibility. "
    "If the page does not describe any concrete incentive program (e.g. a "
    "navigation landing page or generic blog post), return an empty array. "
    "Lower confidence_score whenever wording is ambiguous."
)


USER_PROMPT_TEMPLATE = """Extract every incentive program described on this page.

Source name: {source_name}
Source URL: {source_url}
Content type: {content_type}
Known jurisdiction level: {level}
Known jurisdiction: {jurisdiction}
Known state: {state}
Known county: {county}
Known city: {city}
Known utility: {utility}

Use the jurisdiction hints above to populate the level / state / county / city /
utility_provider fields when the page itself does not restate them. Do not
override these hints with contradictory values invented from generic page text.

Return a JSON object with key "programs" whose value is an array. Each element
must match the IncentivesExtraction schema enforced via response_format. If the
page lists multiple distinct programs, return one element per program. If the
page is not actually about an incentive program, return an empty array.

CONTENT TO EXTRACT FROM:
---
{content}
---
"""


RESPONSE_JSON_SCHEMA: dict = {
    "name": "IncentivesExtraction",
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "programs": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "program_name": {"type": "string"},
                        "category": {"type": ["string", "null"]},
                        "type": {
                            "type": ["string", "null"],
                            "enum": [
                                "tax_credit",
                                "grant",
                                "rebate",
                                "loan",
                                "financing",
                                "exemption",
                                "subsidy",
                                "investment",
                                None,
                            ],
                        },
                        "level": {
                            "type": ["string", "null"],
                            "enum": [
                                "federal",
                                "state",
                                "county",
                                "city",
                                "utility",
                                None,
                            ],
                        },
                        "state": {"type": ["string", "null"]},
                        "county": {"type": ["string", "null"]},
                        "city": {"type": ["string", "null"]},
                        "utility_provider": {"type": ["string", "null"]},
                        "amount_type": {
                            "type": ["string", "null"],
                            "enum": [
                                "fixed_dollar",
                                "percentage",
                                "per_unit",
                                "up_to",
                                "tiered",
                                None,
                            ],
                        },
                        "amount_value": {"type": ["number", "null"]},
                        "amount_max": {"type": ["number", "null"]},
                        "amount_text": {"type": ["string", "null"]},
                        "eligible_property_types": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "eligible_project_types": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "income_required": {"type": ["boolean", "null"]},
                        "income_limit_pct_ami": {"type": ["number", "null"]},
                        "requires_homeownership": {"type": ["boolean", "null"]},
                        "eligibility_notes": {"type": ["string", "null"]},
                        "description": {"type": ["string", "null"]},
                        "application_url": {"type": ["string", "null"]},
                        "program_administrator": {"type": ["string", "null"]},
                        "expires_at": {"type": ["string", "null"]},
                        "confidence_score": {
                            "type": "number",
                            "minimum": 0.0,
                            "maximum": 1.0,
                        },
                    },
                    "required": ["program_name", "confidence_score"],
                },
            }
        },
        "required": ["programs"],
    },
    "strict": False,
}
