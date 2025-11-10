"""Fallback policy engine mapping error types to recovery actions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Literal, Optional

from router.task_types import TaskType

ActionType = Literal[
    "retry",
    "reprompt_strict",
    "shrink_context",
    "switch_model",
    "abort",
]


@dataclass
class FallbackAction:
    action: ActionType
    reason: str
    next_model: Optional[str] = None
    retry_count: int = 0


class FallbackPolicy:
    """Determines fallback actions based on error type and context."""

    def __init__(self, retry_limit: int = 2) -> None:
        self.retry_limit = retry_limit

    def decide(
        self,
        error_type: str,
        task_type: TaskType,
        model_id: str,
        previous_retries: int,
        alternative_model: Optional[str] = None,
    ) -> FallbackAction:
        if previous_retries < self.retry_limit and error_type in {"decode_error", "schema_failure"}:
            return FallbackAction(action="retry", reason="Retrying due to transient parse/schema issue", retry_count=previous_retries + 1)

        if error_type == "no_json_candidate":
            return FallbackAction(action="reprompt_strict", reason="Reprompt with stricter JSON instructions")

        if error_type in {"missing_field", "type_mismatch", "enum_mismatch"}:
            return FallbackAction(action="reprompt_strict", reason="Schema validation failure; enforce stricter JSON response")

        if error_type == "consistency_failed":
            if alternative_model:
                return FallbackAction(action="switch_model", reason="Consistency check failed; switching model", next_model=alternative_model)
            return FallbackAction(action="shrink_context", reason="Consistency failure; reducing context for targeted rerun")

        return FallbackAction(action="abort", reason=f"No fallback available for error {error_type}")
