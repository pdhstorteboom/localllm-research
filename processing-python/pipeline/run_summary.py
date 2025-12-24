"""Capture machine-readable run summaries for pipeline executions."""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Optional

from models.elasticsearch_client import ElasticsearchClient, ElasticsearchError, get_default_elasticsearch_client

logger = logging.getLogger(__name__)


@dataclass
class RunSummaryEntry:
    document_id: str
    model_id: str
    router_reason: str
    batch_events: List[str]
    fallback_events: List[str]
    validation_status: str


@dataclass
class RunSummary:
    entries: List[RunSummaryEntry] = field(default_factory=list)
    es_client: Optional[ElasticsearchClient] = field(default=None, repr=False)
    index_name: str = field(default_factory=lambda: os.getenv("ELASTICSEARCH_INDEX_RUNS", "pipeline-run-summary"))

    def __post_init__(self) -> None:
        if self.es_client is None:
            self.es_client = get_default_elasticsearch_client()

    def add_entry(
        self,
        document_id: str,
        model_id: str,
        router_reason: str,
        batch_events: List[str],
        fallback_events: List[str],
        validation_status: str,
        ) -> None:
        entry = RunSummaryEntry(
            document_id=document_id,
            model_id=model_id,
            router_reason=router_reason,
            batch_events=batch_events,
            fallback_events=fallback_events,
            validation_status=validation_status,
        )
        self.entries.append(entry)
        self._index_entry(entry)

    def flush(self, output_path: str) -> None:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = [asdict(entry) for entry in self.entries]
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _index_entry(self, entry: RunSummaryEntry) -> None:
        if not self.es_client:
            return
        try:
            self.es_client.index_document(self.index_name, asdict(entry))
        except ElasticsearchError as exc:
            logger.warning("Failed to index run summary entry: %s", exc)
