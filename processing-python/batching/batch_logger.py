"""Machine-readable logging for batch execution experiments."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List

from batching.batch_planner import BatchPlan
from batching.executor import BatchResult
from batching.gpu_monitor import GpuStatus


@dataclass
class BatchLog:
    model_id: str
    batch_size: int
    estimated_tokens: int
    actual_tokens: int
    gpu_free_memory_mb: int | None
    success: bool
    error: str | None
    reason: str


class BatchLogger:
    """Collects batch metrics for later analysis."""

    def __init__(self, output_path: str) -> None:
        self.output_path = Path(output_path)
        self.records: List[BatchLog] = []

    def record(self, plan: BatchPlan, result: BatchResult, gpu_status: List[GpuStatus]) -> None:
        gpu_free = gpu_status[0].free_memory_mb if gpu_status else None
        actual_tokens = sum(task.token_estimate for task in plan.tasks)
        self.records.append(
            BatchLog(
                model_id=plan.model_id,
                batch_size=len(plan.tasks),
                estimated_tokens=plan.total_tokens,
                actual_tokens=actual_tokens,
                gpu_free_memory_mb=gpu_free,
                success=result.success,
                error=result.error,
                reason=plan.reason,
            )
        )

    def flush(self) -> None:
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        payload = [asdict(record) for record in self.records]
        with self.output_path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=False)
