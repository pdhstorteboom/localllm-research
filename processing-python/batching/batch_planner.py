"""Adaptive batch planner that groups tasks using model and token budgets."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from batching.gpu_monitor import GpuMonitor
from batching.task import LlmTask


@dataclass
class BatchPlan:
    model_id: str
    tasks: List[LlmTask]
    total_tokens: int
    reason: str


class BatchPlanner:
    """Creates adaptive batches taking GPU status and token limits into account."""

    def __init__(self, gpu_monitor: Optional[GpuMonitor] = None) -> None:
        self.gpu_monitor = gpu_monitor or GpuMonitor()

    def plan(
        self,
        tasks: List[LlmTask],
        max_batch_size: int,
        max_tokens_per_batch: int,
        min_free_memory_mb: int = 0,
    ) -> List[BatchPlan]:
        gpu_status = self.gpu_monitor.sample()
        if gpu_status and gpu_status[0].free_memory_mb < min_free_memory_mb:
            max_batch_size = max(1, max_batch_size // 2)
            max_tokens_per_batch = max(512, max_tokens_per_batch // 2)

        grouped = self._group_by_model(tasks)
        plans: List[BatchPlan] = []

        for model_id, bucket in grouped.items():
            bucket.sort(key=lambda task: task.token_estimate, reverse=True)
            current_batch: List[LlmTask] = []
            token_count = 0

            for task in bucket:
                if (
                    len(current_batch) >= max_batch_size
                    or token_count + task.token_estimate > max_tokens_per_batch
                ):
                    if current_batch:
                        plans.append(
                            BatchPlan(
                                model_id=model_id,
                                tasks=current_batch,
                                total_tokens=token_count,
                                reason="Batch closed due to size or token limit",
                            )
                        )
                    current_batch = []
                    token_count = 0

                current_batch.append(task)
                token_count += task.token_estimate

            if current_batch:
                plans.append(
                    BatchPlan(
                        model_id=model_id,
                        tasks=current_batch,
                        total_tokens=token_count,
                        reason="Batch finalization",
                    )
                )

        return plans

    @staticmethod
    def _group_by_model(tasks: List[LlmTask]) -> Dict[str, List[LlmTask]]:
        grouped: Dict[str, List[LlmTask]] = {}
        for task in tasks:
            key = task.target_model or task.constraints.preferred_model or "unspecified"
            grouped.setdefault(key, []).append(task)
        return grouped
