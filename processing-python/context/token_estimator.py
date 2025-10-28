"""Heuristic token usage estimation for context planning."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional


def estimate_tokens(text: str) -> int:
    """Estimate tokens assuming 4 characters per token."""
    cleaned = text.strip()
    if not cleaned:
        return 0
    return max(1, len(cleaned) // 4)


def estimate_tokens_for_fragments(fragments: Iterable[str]) -> int:
    """Aggregate token estimates for multiple fragments."""
    total = 0
    for fragment in fragments:
        total += estimate_tokens(fragment)
    return total


@dataclass
class TokenStats:
    """Tracks estimated token usage for inputs and outputs."""

    input_tokens: int = 0
    output_tokens: int = 0

    @property
    def total(self) -> int:
        return self.input_tokens + self.output_tokens

    def add_input(self, text: str) -> None:
        self.input_tokens += estimate_tokens(text)

    def add_output(self, text: str) -> None:
        self.output_tokens += estimate_tokens(text)
