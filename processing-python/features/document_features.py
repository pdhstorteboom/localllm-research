"""Expose document features for routing and context selection."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable

from preprocessing.cleaner import NormalizedSection
from preprocessing.structure_detector import StructureDetector, StructureSignals


@dataclass
class DocumentFeatures:
    language: str | None
    character_count: int
    token_estimate: int
    sections: int
    financial_terms: bool

    def as_dict(self) -> Dict[str, object]:
        return {
            "language": self.language,
            "character_count": self.character_count,
            "token_estimate": self.token_estimate,
            "sections": self.sections,
            "financial_terms": self.financial_terms,
        }
