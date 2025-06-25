"""HTML extraction utilities for LLM-ready text."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List, Optional

from bs4 import BeautifulSoup, Tag  # type: ignore


@dataclass
class HtmlSection:
    title: Optional[str] = None
    paragraphs: List[str] = field(default_factory=list)


class HtmlExtractor:
    """Converts HTML documents into structured text without UI boilerplate."""

    def __init__(self, allowed_headings: Optional[Iterable[str]] = None) -> None:
        self.allowed_headings = {name.lower() for name in (allowed_headings or ["h1", "h2", "h3"])}

    def extract(self, html: str) -> List[HtmlSection]:
        soup = BeautifulSoup(html, "html.parser")
        self._drop_boilerplate(soup)

        sections: List[HtmlSection] = []
        current = HtmlSection()

        for node in soup.body.descendants if soup.body else soup.descendants:
            if isinstance(node, Tag) and node.name and node.name.lower() in self.allowed_headings:
                text = self._clean_text(node.get_text())
                if not text:
                    continue
                if current.title or current.paragraphs:
                    sections.append(current)
                current = HtmlSection(title=text)
                continue

            if isinstance(node, Tag) and node.name == "p":
                text = self._clean_text(node.get_text())
                if text:
                    current.paragraphs.append(text)

        if current.title or current.paragraphs:
            sections.append(current)

        return sections

    def _drop_boilerplate(self, soup: BeautifulSoup) -> None:
        for tag_name in ["script", "style", "nav", "footer", "header", "aside", "noscript"]:
            for tag in soup.find_all(tag_name):
                tag.decompose()

        boilerplate_tokens = {"sidebar", "navigation", "cookie", "share", "advertisement"}
        for tag in list(soup.find_all(True)):
            bucket = []
            for attr in ("class", "id"):
                value = tag.get(attr)
                if isinstance(value, str):
                    bucket.append(value.lower())
                elif isinstance(value, list):
                    bucket.extend(v.lower() for v in value if isinstance(v, str))
            if any(token in " ".join(bucket) for token in boilerplate_tokens):
                tag.decompose()

    @staticmethod
    def _clean_text(value: str) -> str:
        if not value:
            return ""
        collapsed = " ".join(value.split())
        return collapsed
