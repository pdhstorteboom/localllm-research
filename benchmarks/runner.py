"""Model-agnostic benchmark runner for PROCESSING-LLM-01."""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Protocol

from benchmarks.result_writer import BenchmarkResult, ResultWriter


class ModelEndpoint(Protocol):
    def __call__(self, model_id: str, task_type: str, document: str) -> dict:
        ...


@dataclass
class BenchmarkRequest:
    model_id: str
    task_type: str
    document_id: str
    document_path: str


class BenchmarkRunner:
    """Executes benchmark tasks against a provided model endpoint."""

    def __init__(self, endpoint: ModelEndpoint, writer: ResultWriter, timeout_s: float = 120.0) -> None:
        self.endpoint = endpoint
        self.writer = writer
        self.timeout_s = timeout_s

    def run(self, requests: Iterable[BenchmarkRequest]) -> List[BenchmarkResult]:
        results: List[BenchmarkResult] = []
        for request in requests:
            raw_text = Path(request.document_path).read_text(encoding="utf-8")
            started = time.time()
            error: str | None = None
            output_tokens = 0
            try:
                output = self._invoke_with_timeout(request, raw_text)
                output_tokens = int(output.get("output_tokens", 0))
            except Exception as exc:  # noqa: BLE001
                error = str(exc)
            finished = time.time()

            result = BenchmarkResult(
                model_id=request.model_id,
                task_type=request.task_type,
                document_id=request.document_id,
                started_at=started,
                finished_at=finished,
                input_tokens=self._estimate_tokens(raw_text),
                output_tokens=output_tokens,
                error=error,
            )
            self.writer.add(result)
            results.append(result)

        self.writer.flush()
        return results

    def _invoke_with_timeout(self, request: BenchmarkRequest, raw_text: str) -> dict:
        start = time.time()
        output = self.endpoint(request.model_id, request.task_type, raw_text)
        elapsed = time.time() - start
        if elapsed > self.timeout_s:
            raise TimeoutError(f"Task exceeded timeout {self.timeout_s}s")
        return output

    
