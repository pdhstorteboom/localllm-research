"""Token budget management per model and task."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from context.token_estimator import TokenStats, estimate_tokens


@dataclass
class Budget:
    max_input_tokens: int
    max_output_tokens: int
    safety_margin: float = 0.1

    def remaining_input(self, used_tokens: int) -> int:
        limit = int(self.max_input_tokens * (1 - self.safety_margin))
        return max(0, limit - used_tokens)

    def remaining_output(self, used_tokens: int) -> int:
        limit = int(self.max_output_tokens * (1 - self.safety_margin))
        return max(0, limit - used_tokens)


class TokenBudgetManager:
    """Manages budgets for multiple models and tasks."""

    def __init__(self) -> None:
        self._budgets: Dict[str, Budget] = {}

    def register_budget(self, model_id: str, budget: Budget) -> None:
        self._budgets[model_id] = budget

    def get_budget(self, model_id: str) -> Optional[Budget]:
        return self._budgets.get(model_id)

    def can_accommodate(self, model_id: str, prompt: str, expected_output_tokens: int) -> bool:
        budget = self.get_budget(model_id)
        if not budget:
            return False
        stats = TokenStats(input_tokens=estimate_tokens(prompt), output_tokens=expected_output_tokens)
        return (
            stats.input_tokens <= budget.remaining_input(0)
            and stats.output_tokens <= budget.remaining_output(0)
        )

    def consume(self, model_id: str, stats: TokenStats) -> bool:
        budget = self.get_budget(model_id)
        if not budget:
            return False
        if (
            stats.input_tokens > budget.remaining_input(0)
            or stats.output_tokens > budget.remaining_output(0)
        ):
            return False
        # In this heuristic version we do not persist usage per request.
        return True
