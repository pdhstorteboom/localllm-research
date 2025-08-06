"""Data models inputs needed for routing decisions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from benchmarks.model_profile import ModelProfile
from features.document_features import DocumentFeatures
from router.task_types import TaskType


@dataclass
class Constraints:
    """Optional constraints such as latency budgets or token caps."""

    max_latency_ms: Optional[float] = None
    max_tokens: Optional[int] = None
    hardware_slot: Optional[str] = None


@dataclass
class CandidateModel:
    """Candidate model enriched with profiling data."""

    model_id: str
    profile: Optional[ModelProfile] = None
    expected_latency_ms: Optional[float] = None
    expected_tokens: Optional[int] = None
    failure_rate: Optional[float] = None
    annotations: Dict[str, str] = field(default_factory=dict)


@dataclass
class RouterInputs:
    """Complete input bundle that feeds routing logic."""

    document_features: DocumentFeatures
    task_type: TaskType
    candidate_models: List[CandidateModel]
    constraints: Constraints = field(default_factory=Constraints)

    def candidate_ids(self) -> List[str]:
        return [candidate.model_id for candidate in self.candidate_models]
