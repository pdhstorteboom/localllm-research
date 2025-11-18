"""Capture machine-readable run summaries for pipeline executions."""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Optional


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

    def add_entry(
        self,
        document_id: str,
        model_id: str,
        router_reason: str,
        batch_events: List[str],
        fallback_events: List[str],
        validation_status: str,
    ) -> None:
        self.entries.append(
            RunSummaryEntry(
                document_id=document_id,
                model_id=model_id,
                router_reason=router_reason,
                batch_events=batch_events,
                fallback_events=fallback_events,
                validation_status=validation_status,
            )
        )

    def flush(self, output_path: str) -> None:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = [asdict(entry) for entry in self.entries]
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
