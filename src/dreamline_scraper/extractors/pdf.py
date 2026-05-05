"""Lightweight PDF text extraction helper."""

from __future__ import annotations

import io
import logging
from typing import Optional

LOGGER = logging.getLogger(__name__)


def extract_pdf_text(content: bytes) -> Optional[str]:
    """Return the concatenated text of a PDF, or ``None`` on failure.

    Uses :mod:`pdfplumber` lazily so the dependency is only required when a
    scraper actually hits a PDF page.
    """

    try:
        import pdfplumber  # type: ignore
    except ImportError:  # pragma: no cover - optional path
        LOGGER.warning("pdfplumber not installed; cannot extract PDF text")
        return None
    try:
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            chunks = []
            for page in pdf.pages:
                text = page.extract_text() or ""
                if text:
                    chunks.append(text)
        return "\n\n".join(chunks).strip() or None
    except Exception as exc:  # pragma: no cover - PDF parser quirks
        LOGGER.warning("PDF extraction failed: %s", exc)
        return None
