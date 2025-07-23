"""Utility to persist benchmark results as JSON."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List


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

    def __init__(self, output_path: str) -> None:
        self.output_path = Path(output_path)
        self.records: List[BenchmarkResult] = []

    def add(self, result: BenchmarkResult) -> None:
        self.records.append(result)

    def flush(self) -> None:
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        payload = [asdict(record) | {"duration_ms": record.duration_ms()} for record in self.records]
        with self.output_path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=False)
