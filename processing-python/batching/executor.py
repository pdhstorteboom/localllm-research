"""Batch execution controller with fallback strategies."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Callable, List, Optional

from batching.batch_planner import BatchPlan
from batching.task import LlmTask

logger = logging.getLogger(__name__)


class ExecutionError(Exception):
    pass


@dataclass
class BatchResult:
    plan: BatchPlan
    success: bool
    error: Optional[str] = None


class BatchExecutor:
    """Executes planned batches and applies fallback strategies upon failure."""

    def __init__(self, inference_fn: Callable[[BatchPlan], None], fallback_fn: Optional[Callable[[List[LlmTask]], None]] = None) -> None:
        self.inference_fn = inference_fn
        self.fallback_fn = fallback_fn

    def execute(self, plans: List[BatchPlan]) -> List[BatchResult]:
        results: List[BatchResult] = []
        for plan in plans:
            try:
                self.inference_fn(plan)
                results.append(BatchResult(plan=plan, success=True))
            except ExecutionError as exc:
                results.append(BatchResult(plan=plan, success=False, error=str(exc)))
                fallback_plans = self._fallback(plan, str(exc))
                for fallback_plan in fallback_plans:
                    try:
                        self.inference_fn(fallback_plan)
                        results.append(BatchResult(plan=fallback_plan, success=True))
                    except ExecutionError as fallback_exc:
                        results.append(BatchResult(plan=fallback_plan, success=False, error=str(fallback_exc)))
        return results

    def _fallback(self, plan: BatchPlan, reason: str) -> List[BatchPlan]:
        logger.warning("Batch failed: %s", reason)
        if "OOM" in reason.upper():
            return self._split_batch(plan)
        if self.fallback_fn:
            self.fallback_fn(plan.tasks)
        return []

    def _split_batch(self, plan: BatchPlan) -> List[BatchPlan]:
        if len(plan.tasks) <= 1:
            return []
        mid = len(plan.tasks) // 2
        return [
            BatchPlan(model_id=plan.model_id, tasks=plan.tasks[:mid], total_tokens=sum(t.token_estimate for t in plan.tasks[:mid]), reason="Fallback split part A"),
            BatchPlan(model_id=plan.model_id, tasks=plan.tasks[mid:], total_tokens=sum(t.token_estimate for t in plan.tasks[mid:]), reason="Fallback split part B"),
        ]
