"""Simple heuristic router for PROCESSING-LLM-01."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from router.router_inputs import CandidateModel, Constraints, RouterInputs
from router.task_types import TaskType


@dataclass
class RoutingDecision:
    model_id: Optional[str]
    reason: str
