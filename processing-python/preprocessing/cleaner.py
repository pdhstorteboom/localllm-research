"""Text cleaning helpers to normalize extracted content for LLM processing."""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Iterable, List, Optional, Protocol


class SectionLike(Protocol):
    title: Optional[str]
    paragraphs: List[str]


@dataclass
class NormalizedSection:
    title: Optional[str] = None
    paragraphs: List[str] = field(default_factory=list)


class TextCleaner:
    """Cleans extracted text to keep LLM context windows efficient."""

    def __init__(self, min_paragraph_length: int = 25, banned_phrases: Optional[Iterable[str]] = None) -> None:
        self.min_paragraph_length = min_paragraph_length
        self.banned_patterns = [re.compile(re.escape(p), re.IGNORECASE) for p in (banned_phrases or [])]

    def normalize_sections(self, sections: Iterable[SectionLike]) -> List[NormalizedSection]:
        normalized: List[NormalizedSection] = []
        for section in sections:
            clean_paragraphs = [self._clean_paragraph(p) for p in section.paragraphs]
            clean_paragraphs = [p for p in clean_paragraphs if len(p) >= self.min_paragraph_length]
            if not clean_paragraphs:
                continue
            normalized.append(NormalizedSection(title=section.title, paragraphs=clean_paragraphs))
        return normalized

    def as_llm_ready_text(self, sections: Iterable[SectionLike]) -> str:
        normalized = self.normalize_sections(sections)
        chunks: List[str] = []
        for section in normalized:
            if section.title:
                chunks.append(section.title.strip())
            chunks.extend(section.paragraphs)
        return "\n\n".join(chunks)

    def _clean_paragraph(self, paragraph: str) -> str:
        collapsed = " ".join(paragraph.split())
        for pattern in self.banned_patterns:
            collapsed = pattern.sub("", collapsed)
        collapsed = re.sub(r"\s{2,}", " ", collapsed)
        return collapsed.strip()
