"""Orchestrator applying fallback policies and logging decisions."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from router.task_types import TaskType
from validation.fallback_policy import FallbackAction, FallbackPolicy

logger = logging.getLogger(__name__)


@dataclass
class FallbackContext:
    task_type: TaskType
    model_id: str
    alternative_model: Optional[str] = None


class FallbackOrchestrator:
    def __init__(self, policy: Optional[FallbackPolicy] = None) -> None:
        self.policy = policy or FallbackPolicy()

    def handle_error(
        self,
        error_type: str,
        context: FallbackContext,
        previous_retries: int,
    ) -> FallbackAction:
        action = self.policy.decide(
            error_type=error_type,
            task_type=context.task_type,
            model_id=context.model_id,
            previous_retries=previous_retries,
            alternative_model=context.alternative_model,
        )
        self._log_decision(action, context, error_type)
        return action

    def _log_decision(self, action: FallbackAction, context: FallbackContext, error_type: str) -> None:
        logger.info(
            "Fallback decision: action=%s model=%s error=%s reason=%s next_model=%s retries=%s",
            action.action,
            context.model_id,
            error_type,
            action.reason,
            action.next_model,
            action.retry_count,
        )
