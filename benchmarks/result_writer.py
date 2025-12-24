"""Utility to persist benchmark results as JSON and Elasticsearch."""

from __future__ import annotations

import json
import logging
import os
from dataclasses import asdict, dataclass
from pathlib import Path
import sys
from typing import List, Optional

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSING_PATH = PROJECT_ROOT / "processing-python"
if str(PROCESSING_PATH) not in sys.path:
    sys.path.insert(0, str(PROCESSING_PATH))

from models.elasticsearch_client import ElasticsearchClient, ElasticsearchError, get_default_elasticsearch_client

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkResult:
    model_id: str
    task_type: str
    document_id: str
    started_at: float
    finished_at: float
    input_tokens: int
    output_tokens: int
    error: str | None

    def duration_ms(self) -> float:
        return (self.finished_at - self.started_at) * 1000.0


class ResultWriter:
    """Stores benchmark outputs per document."""

    def __init__(
        self,
        output_path: str,
        es_client: Optional[ElasticsearchClient] = None,
        index_name: Optional[str] = None,
    ) -> None:
        self.output_path = Path(output_path)
        self.records: List[BenchmarkResult] = []
        self.es_client = es_client or get_default_elasticsearch_client()
        self.index_name = index_name or os.getenv("ELASTICSEARCH_INDEX_BENCHMARKS", "benchmark-results")

    def add(self, result: BenchmarkResult) -> None:
        self.records.append(result)
        self._index_result(result)

    def flush(self) -> None:
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        payload = [self._result_payload(record) for record in self.records]
        with self.output_path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=False)

    def _result_payload(self, result: BenchmarkResult) -> dict:
        return asdict(result) | {"duration_ms": result.duration_ms()}

    def _index_result(self, result: BenchmarkResult) -> None:
        if not self.es_client:
            return
        try:
            self.es_client.index_document(self.index_name, self._result_payload(result))
        except ElasticsearchError as exc:
            logger.warning("Failed to index benchmark result: %s", exc)
