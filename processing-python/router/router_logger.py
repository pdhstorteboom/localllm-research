"""Machine-readable logging for routing decisions."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterable, List

from router.router_inputs import CandidateModel, RouterInputs
from router.heuristic_router import RoutingDecision


@dataclass
class CandidateLog:
    model_id: str
    reason: str


@dataclass
class DecisionLog:
    document_features: dict
    task_type: str
    constraints: dict
    chosen_model: str | None
    candidates: List[CandidateLog] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "document_features": self.document_features,
            "task_type": self.task_type,
            "constraints": self.constraints,
            "chosen_model": self.chosen_model,
            "candidates": [asdict(candidate) for candidate in self.candidates],
        }


class RouterLogger:
    """Collects routing decisions for auditability."""

    def __init__(self, output_path: str) -> None:
        self.output_path = Path(output_path)
        self.records: List[DecisionLog] = []

    def record(self, inputs: RouterInputs, decision: RoutingDecision) -> None:
        candidate_logs = [CandidateLog(model_id=c.model_id, reason=c.annotations.get("reason", "n/a")) for c in inputs.candidate_models]
        log_entry = DecisionLog(
            document_features=inputs.document_features.as_dict() if hasattr(inputs.document_features, "as_dict") else inputs.document_features.__dict__,
            task_type=inputs.task_type.value,
            constraints=asdict(inputs.constraints),
            chosen_model=decision.model_id,
            candidates=candidate_logs,
        )
        self.records.append(log_entry)

    def flush(self) -> None:
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        payload = [record.as_dict() for record in self.records]
        with self.output_path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=False)
