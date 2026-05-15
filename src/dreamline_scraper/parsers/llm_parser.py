"""OpenAI-backed structured-output parser for incentive pages."""

from __future__ import annotations

import json
import logging
from datetime import date
from typing import List, Optional

from pydantic import ValidationError

from ..config import Settings, load_settings
from ..schema import RawIncentive
from ..sources import Source
from .prompts import RESPONSE_JSON_SCHEMA, SYSTEM_PROMPT, USER_PROMPT_TEMPLATE

LOGGER = logging.getLogger(__name__)


def _model_locks_temperature(model: str) -> bool:
    if not model:
        return False
    name = model.lower()
    return name.startswith(("o1", "o3", "o4", "gpt-5"))


class LLMParser:
    """Wraps the OpenAI Chat Completions API with structured outputs."""

    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or load_settings()
        self._client = None

    @property
    def enabled(self) -> bool:
        return bool(self.settings.openai_api_key)

    def parse(
        self,
        *,
        content: str,
        source: Source,
        final_url: str,
        content_type: str = "html_text",
        max_chars: int = 16000,
    ) -> List[RawIncentive]:
        """Send content to the LLM and return parsed RawIncentive records."""

        if not self.enabled:
            LOGGER.info("LLM disabled (no OPENAI_API_KEY); skipping %s", source.url)
            return []
        if not content or len(content.strip()) < 40:
            return []

        client = self._get_client()
        if client is None:
            return []

        user_prompt = USER_PROMPT_TEMPLATE.format(
            source_name=source.name,
            source_url=final_url or source.url,
            content_type=content_type,
            level=source.level or "",
            jurisdiction=source.jurisdiction,
            state=source.state or "",
            county=source.county or "",
            city=source.city or "",
            utility=source.utility or "",
            content=content[:max_chars],
        )
        request_kwargs = {
            "model": self.settings.openai_model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": RESPONSE_JSON_SCHEMA,
            },
        }
        if not _model_locks_temperature(self.settings.openai_model):
            request_kwargs["temperature"] = 0.0

        try:
            response = client.chat.completions.create(**request_kwargs)
        except Exception as exc:
            LOGGER.warning("OpenAI request failed for %s: %s", source.url, exc)
            return []

        try:
            payload = response.choices[0].message.content or "{}"
            data = json.loads(payload)
        except (json.JSONDecodeError, AttributeError, IndexError) as exc:
            LOGGER.warning("Bad LLM JSON for %s: %s", source.url, exc)
            return []

        programs = data.get("programs") or []
        return list(self._coerce_records(programs, source=source, final_url=final_url))

    def _get_client(self):
        if self._client is not None:
            return self._client
        try:
            from openai import OpenAI  # type: ignore
        except ImportError:  # pragma: no cover
            LOGGER.warning("openai package not installed; LLM parsing disabled")
            return None
        self._client = OpenAI(api_key=self.settings.openai_api_key)
        return self._client

    def _coerce_records(self, programs: list, *, source: Source, final_url: str):
        today = date.today().isoformat()
        for entry in programs:
            if not isinstance(entry, dict):
                continue
            entry.setdefault("source_url", final_url or source.url)
            entry.setdefault("last_verified_at", today)
            entry.setdefault("level", source.level or None)
            entry.setdefault("state", source.state or None)
            if source.county and not entry.get("county"):
                entry["county"] = source.county
            if source.city and not entry.get("city"):
                entry["city"] = source.city
            if source.utility and not entry.get("utility_provider"):
                entry["utility_provider"] = source.utility
            entry["extraction_source"] = "llm"
            try:
                yield RawIncentive.model_validate(entry)
            except ValidationError as exc:
                LOGGER.info("LLM record rejected for %s: %s", source.url, exc)
