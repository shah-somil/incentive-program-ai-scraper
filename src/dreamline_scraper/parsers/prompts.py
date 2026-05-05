"""Prompt templates for LLM-based incentive extraction.

Mirrors the template in brief Section 14.3.
"""

from __future__ import annotations


SYSTEM_PROMPT = (
    "You are a structured data extraction specialist. Extract incentive program "
    "details from the provided content and return JSON that matches the schema "
    "exactly. Only extract information explicitly stated in the content. If a "
    "field is not mentioned, return null for that field. Never infer or assume "
    "values. Do not hallucinate amounts, deadlines, or eligibility criteria. "
    "Treat ambiguous wording conservatively and lower the confidence score."
)


USER_PROMPT_TEMPLATE = """Extract every distinct incentive program described in the
following content scraped from {source_url}.

Source name: {source_name}
Content type: {content_type}

Return a JSON object with key "programs" whose value is an array. Each array
element must match the IncentiveSchema schema enforced via response_format.
For every program include a confidence_score between 0.0 and 1.0 reflecting
how certain you are about the extracted values. If the page is not actually an
incentive program (e.g. a generic blog post), return an empty array.

CONTENT TO EXTRACT FROM:
---
{content}
---
"""


# JSON schema used with OpenAI structured outputs.  We keep it deliberately
# permissive so the model never has to choose between "be wrong" and "fail to
# return JSON".  All strings/numbers are nullable; downstream Pydantic
# validation re-enforces stricter rules where it can.
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
