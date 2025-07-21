"""Utilities for logging preprocessing metrics for WBSO experiments."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, List, Optional

from preprocessing.cleaner import NormalizedSection
from features.document_features import DocumentFeatures


@dataclass
class PreprocessRecord:
    document_id: str
    original_length: int
    cleaned_length: int
    token_estimate: int
    sections: int
    language: Optional[str]
    financial_terms: bool
    errors: List[str]


class PreprocessLogger:
    """Collects preprocessing metrics and writes them as machine-readable JSON."""

    def __init__(self, output_path: str) -> None:
        self.output_path = Path(output_path)
        self.records: List[PreprocessRecord] = []

    def log_result(
        self,
        document_id: str,
        raw_text: str,
        sections: Iterable[NormalizedSection],
        features: DocumentFeatures,
        errors: Optional[Iterable[str]] = None,
    ) -> None:
        cleaned_text = self._sections_to_text(sections)
        record = PreprocessRecord(
            document_id=document_id,
            original_length=len(raw_text),
            cleaned_length=len(cleaned_text),
            token_estimate=features.token_estimate,
            sections=features.sections,
            language=features.language,
            financial_terms=features.financial_terms,
            errors=list(errors or []),
        )
        self.records.append(record)

    def flush(self) -> None:
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        payload = [asdict(record) for record in self.records]
        with self.output_path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=False)

    @staticmethod
    def _sections_to_text(sections: Iterable[NormalizedSection]) -> str:
        chunks: List[str] = []
        for section in sections:
            if section.title:
                chunks.append(section.title)
            chunks.extend(section.paragraphs)
        return "\n".join(chunks)
