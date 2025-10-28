"""Select relevant sections within token budgets per task."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

from context.token_budget import Budget
from context.token_estimator import estimate_tokens
from router.task_types import TaskType
from preprocessing.structure_detector import NormalizedSection  # type: ignore


@dataclass
class SelectionResult:
    section: NormalizedSection
    reason: str
    token_estimate: int


class SectionSelector:
    """Chooses document sections while respecting token constraints."""

    def __init__(self, budget: Budget) -> None:
        self.budget = budget

    def select(self, sections: Iterable[NormalizedSection], task_type: TaskType) -> List[SelectionResult]:
        remaining = self.budget.remaining_input(0)
        selected: List[SelectionResult] = []

        for section in sections:
            text = "\n".join(section.paragraphs)
            tokens = estimate_tokens(text)
            if tokens == 0:
                continue

            if tokens > remaining:
                reason = f"Skipped {section.title or 'untitled'} due to token limit"
                selected.append(SelectionResult(section=section, reason=reason, token_estimate=0))
                break

            justification = self._justify(section, task_type)
            selected.append(
                SelectionResult(section=section, reason=justification, token_estimate=tokens)
            )
            remaining -= tokens

        return selected

    def _justify(self, section: NormalizedSection, task_type: TaskType) -> str:
        title = section.title or "untitled"
        if task_type == TaskType.EXTRACTION and section.title and "financial" in section.title.lower():
            return f"Included {title} because task requires financial signals"
        if task_type == TaskType.SUMMARIZATION:
            return f"Included {title} to preserve narrative continuity"
        return f"Included {title} based on sequential allocation"
