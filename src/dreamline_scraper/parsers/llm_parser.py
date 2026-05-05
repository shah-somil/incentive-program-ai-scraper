"""OpenAI-backed structured-output parser for unstructured incentive pages."""

from __future__ import annotations

import json
import logging
from datetime import date
from typing import List, Optional

from pydantic import ValidationError

from ..config import Settings, load_settings
from ..schema import RawIncentive
from .prompts import RESPONSE_JSON_SCHEMA, SYSTEM_PROMPT, USER_PROMPT_TEMPLATE

LOGGER = logging.getLogger(__name__)


class LLMParser:
    """Wraps the OpenAI Chat Completions API with structured outputs."""

    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or load_settings()
        self._client = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def enabled(self) -> bool:
        return bool(self.settings.openai_api_key)

    def parse(
        self,
        *,
        content: str,
        source_url: str,
        source_name: str,
        content_type: str = "html_text",
        max_chars: int = 16000,
    ) -> List[RawIncentive]:
        """Send content to the LLM and return parsed RawIncentive records."""

        if not self.enabled:
            LOGGER.info("LLM parser disabled (no OPENAI_API_KEY); skipping %s", source_url)
            return []
        if not content or len(content.strip()) < 40:
            return []

        truncated = content[:max_chars]
        client = self._get_client()
        if client is None:
            return []

        user_prompt = USER_PROMPT_TEMPLATE.format(
            source_url=source_url,
            source_name=source_name,
            content_type=content_type,
            content=truncated,
        )
        try:
            response = client.chat.completions.create(
                model=self.settings.openai_model,
                temperature=0.0,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": RESPONSE_JSON_SCHEMA,
                },
            )
        except Exception as exc:
            LOGGER.warning("OpenAI request failed for %s: %s", source_url, exc)
            return []

        try:
            payload = response.choices[0].message.content or "{}"
            data = json.loads(payload)
        except (json.JSONDecodeError, AttributeError, IndexError) as exc:
            LOGGER.warning("Bad LLM JSON for %s: %s", source_url, exc)
            return []

        programs = data.get("programs") or []
        return list(self._coerce_records(programs, source_url=source_url))

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _get_client(self):
        if self._client is not None:
            return self._client
        try:
            from openai import OpenAI  # type: ignore
        except ImportError:  # pragma: no cover - dep missing
            LOGGER.warning("openai package not installed; LLM parsing disabled")
            return None
        self._client = OpenAI(api_key=self.settings.openai_api_key)
        return self._client

    def _coerce_records(self, programs: list, *, source_url: str):
        today = date.today().isoformat()
        for entry in programs:
            if not isinstance(entry, dict):
                continue
            entry.setdefault("source_url", source_url)
            entry.setdefault("last_verified_at", today)
            try:
                yield RawIncentive.model_validate(entry)
            except ValidationError as exc:
                LOGGER.info("LLM record rejected for %s: %s", source_url, exc)
