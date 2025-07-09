"""Derive document structure signals from normalized sections."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional

import langdetect  # type: ignore

from preprocessing.cleaner import NormalizedSection

FINANCE_TERMS = {
    "revenue",
    "earnings",
    "ebitda",
    "cash flow",
    "dividend",
    "liabilities",
    "assets",
    "operating income",
    "net income",
    "guidance",
}


@dataclass
class StructureSignals:
    language: Optional[str]
    character_count: int
    token_estimate: int
    sections: int
    financial_terms: bool


class StructureDetector:
    """Derives structural metadata from normalized sections."""

    def __init__(self, finance_terms: Optional[Iterable[str]] = None) -> None:
        if finance_terms:
            self.finance_terms = {term.lower() for term in finance_terms}
        else:
            self.finance_terms = FINANCE_TERMS

    def analyze(self, sections: Iterable[NormalizedSection]) -> StructureSignals:
        aggregated_text = []
        section_count = 0
        contains_finance = False

        for section in sections:
            section_count += 1
            if section.title:
                aggregated_text.append(section.title)
            aggregated_text.extend(section.paragraphs)
            if not contains_finance and self._has_financial_terms(section):
                contains_finance = True

        joined = "\n".join(aggregated_text)
        language = self._detect_language(joined) if joined else None
        character_count = len(joined)
        token_estimate = self._estimate_tokens(joined)

        return StructureSignals(
            language=language,
            character_count=character_count,
            token_estimate=token_estimate,
            sections=section_count,
            financial_terms=contains_finance,
        )

    def _has_financial_terms(self, section: NormalizedSection) -> bool:
            haystack = " ".join(filter(None, [section.title, *section.paragraphs])).lower()
            return any(term in haystack for term in self.finance_terms)

        @staticmethod
        def _detect_language(text: str) -> Optional[str]:
            try:
                return langdetect.detect(text)
            except (langdetect.lang_detect_exception.LangDetectException, ValueError):  # type: ignore
                return None

        @staticmethod
        def _estimate_tokens(text: str) -> int:
            # Rough heuristic aligned with 4 characters per token to keep compute light.
            return max(1, len(text) // 4)