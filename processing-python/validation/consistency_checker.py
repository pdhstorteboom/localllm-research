"""Consistency checks between input context and LLM output."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable, List, Sequence


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


@dataclass
class ConsistencySignal:
    name: str
    passed: bool
    confidence: float
    reason: str


@dataclass
class ConsistencyResult:
    passed: bool
    signals: List[ConsistencySignal] = field(default_factory=list)

    def add_signal(self, signal: ConsistencySignal) -> None:
        self.signals.append(signal)

    @property
    def reasons(self) -> List[str]:
        return [signal.reason for signal in self.signals if not signal.passed]


class ConsistencyChecker:
    """Provides heuristics to judge whether output aligns with input context."""

    def check_entities(self, context: str, entities: Iterable[str]) -> ConsistencySignal:
        entity_list = list(entities)
        normalized_context = normalize(context)
        missing = []
        for entity in entity_list:
            if normalize(entity) not in normalized_context:
                missing.append(entity)
        passed = len(missing) == 0
        reason = (
            "All required entities found in context"
            if passed
            else f"Missing entities: {', '.join(missing)}"
        )
        total = len(entity_list) if entity_list else 1
        confidence = 1.0 if passed else max(0.1, 1 - len(missing) / total)
        return ConsistencySignal(
            name="required_entities",
            passed=passed,
            confidence=confidence,
            reason=reason,
        )

    def check_keywords(self, context: str, keywords: Sequence[str], min_overlap: int = 1) -> ConsistencySignal:
        normalized_context = normalize(context)
        overlap = sum(1 for keyword in keywords if normalize(keyword) in normalized_context)
        passed = overlap >= min_overlap
        reason = (
            f"Overlap count {overlap} meets threshold {min_overlap}"
            if passed
            else f"Overlap {overlap} below threshold {min_overlap}"
        )
        confidence = min(1.0, overlap / max(1, min_overlap))
        return ConsistencySignal(
            name="keyword_overlap",
            passed=passed,
            confidence=confidence,
            reason=reason,
        )

    def evaluate(self, context: str, required_entities: Iterable[str], keywords: Sequence[str]) -> ConsistencyResult:
        result = ConsistencyResult(passed=True)
        entity_signal = self.check_entities(context, required_entities)
        keyword_signal = self.check_keywords(context, keywords)
        result.add_signal(entity_signal)
        result.add_signal(keyword_signal)
        result.passed = all(signal.passed for signal in result.signals)
        return result
