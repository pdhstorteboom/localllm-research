"""Machine-readable logging for batch execution experiments."""

from __future__ import annotations

import json
import logging
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List, Optional

from batching.batch_planner import BatchPlan
from batching.executor import BatchResult
from batching.gpu_monitor import GpuStatus
from models.elasticsearch_client import ElasticsearchClient, ElasticsearchError, get_default_elasticsearch_client

logger = logging.getLogger(__name__)


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

    def __init__(
        self,
        output_path: str,
        es_client: Optional[ElasticsearchClient] = None,
        index_name: Optional[str] = None,
    ) -> None:
        self.output_path = Path(output_path)
        self.records: List[BatchLog] = []
        self.es_client = es_client or get_default_elasticsearch_client()
        self.index_name = index_name or os.getenv("ELASTICSEARCH_INDEX_BATCH", "batch-events")

    def record(self, plan: BatchPlan, result: BatchResult, gpu_status: List[GpuStatus]) -> None:
        gpu_free = gpu_status[0].free_memory_mb if gpu_status else None
        actual_tokens = sum(task.token_estimate for task in plan.tasks)
        record = BatchLog(
            model_id=plan.model_id,
            batch_size=len(plan.tasks),
            estimated_tokens=plan.total_tokens,
            actual_tokens=actual_tokens,
            gpu_free_memory_mb=gpu_free,
            success=result.success,
            error=result.error,
            reason=plan.reason,
        )
        self.records.append(record)
        self._index_record(record)

    def flush(self) -> None:
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        payload = [asdict(record) for record in self.records]
        with self.output_path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=False)

    def _index_record(self, record: BatchLog) -> None:
        if not self.es_client:
            return
        try:
            self.es_client.index_document(self.index_name, asdict(record))
        except ElasticsearchError as exc:
            logger.warning("Failed to index batch log: %s", exc)
