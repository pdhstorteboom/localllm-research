"""PDF extraction utilities tailored for downstream LLM processing."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from pdfminer.high_level import extract_pages  # type: ignore
from pdfminer.layout import LAParams, LTChar, LTTextContainer  # type: ignore


@dataclass
class Section:
    title: Optional[str] = None
    paragraphs: List[str] = field(default_factory=list)


class PdfExtractor:
    """Extracts structured text from PDFs while removing boilerplate segments."""

    def __init__(self, header_footer_margin: float = 40.0, laparams: Optional[LAParams] = None) -> None:
        self.header_footer_margin = header_footer_margin
        self.laparams = laparams or LAParams(line_overlap=0.5, char_margin=2.0, line_margin=0.5)

    def extract(self, pdf_path: str) -> List[Section]:
        sections: List[Section] = []
        current = Section()

        for page_layout in extract_pages(pdf_path, laparams=self.laparams):
            height = getattr(page_layout, "height", None)
            for element in page_layout:
                if not isinstance(element, LTTextContainer):
                    continue

                if height is not None and (
                    element.y1 > height - self.header_footer_margin or element.y0 < self.header_footer_margin
                ):
                    continue

                text = element.get_text().strip()
                if not text:
                    continue

                if self._looks_like_heading(element):
                    if current.title or current.paragraphs:
                        sections.append(current)
                    current = Section(title=" ".join(text.split()))
                    continue

                normalized = self._normalize_paragraph(text)
                if not normalized:
                    continue
                current.paragraphs.append(normalized)

        if current.title or current.paragraphs:
            sections.append(current)

        return sections

    def _looks_like_heading(self, container: LTTextContainer) -> bool:
        text = container.get_text().strip()
        if len(text) > 160 or len(text) < 3:
            return False

        chars: List[float] = []
        for line in container:
            for char in getattr(line, "_objs", []):
                if isinstance(char, LTChar):
                    chars.append(char.size)

        if not chars:
            return False

        avg_size = sum(chars) / len(chars)
        median_line_size = sorted(chars)[len(chars) // 2]
        uppercase_ratio = self._uppercase_ratio(text)

        return uppercase_ratio > 0.6 or avg_size > median_line_size * 1.1

    @staticmethod
    def _uppercase_ratio(text: str) -> float:
        letters = [c for c in text if c.isalpha()]
        if not letters:
            return 0.0
        upper = sum(1 for c in letters if c.isupper())
        return upper / len(letters)

    @staticmethod
    def _normalize_paragraph(text: str) -> str:
        collapsed = " ".join(text.split())
        if len(collapsed) < 10:
            return ""
        return collapsed
