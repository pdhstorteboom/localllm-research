"""Chunking utilities tailored for downstream LLM processing."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional

from preprocessing.structure_detector import NormalizedSection  # type: ignore
from context.token_estimator import estimate_tokens


@dataclass
class Chunk:
    text: str
    start_offset: int
    end_offset: int
    section_title: Optional[str]
    token_estimate: int


class Chunker:
    """Splits documents into token-aware chunks."""

    def __init__(self, max_tokens: int = 512, overlap_tokens: int = 64) -> None:
        self.max_tokens = max_tokens
        self.overlap_tokens = overlap_tokens

    def chunk_text(self, text: str) -> List[Chunk]:
        chunks: List[Chunk] = []
        start = 0
        length = len(text)

        while start < length:
            end = min(length, start + self.max_tokens * 4)
            chunk_text = text[start:end]
            token_estimate = estimate_tokens(chunk_text)
            chunks.append(
                Chunk(
                    text=chunk_text,
                    start_offset=start,
                    end_offset=end,
                    section_title=None,
                    token_estimate=token_estimate,
                )
            )
            start = end - self.overlap_tokens * 4
        return chunks

    def chunk_sections(self, sections: Iterable[NormalizedSection]) -> List[Chunk]:
        chunks: List[Chunk] = []
        offset = 0
        for section in sections:
            buffer = []
            for paragraph in section.paragraphs:
                buffer.append(paragraph)
                joined = "\n".join(buffer)
                tokens = estimate_tokens(joined)
                if tokens >= self.max_tokens:
                    text = "\n".join(buffer)
                    chunks.append(
                        Chunk(
                            text=text,
                            start_offset=offset,
                            end_offset=offset + len(text),
                            section_title=section.title,
                            token_estimate=estimate_tokens(text),
                        )
                    )
                    offset += len(text)
                    buffer = []
            if buffer:
                text = "\n".join(buffer)
                chunks.append(
                    Chunk(
                        text=text,
                        start_offset=offset,
                        end_offset=offset + len(text),
                        section_title=section.title,
                        token_estimate=estimate_tokens(text),
                    )
                )
                offset += len(text)

        return chunks
