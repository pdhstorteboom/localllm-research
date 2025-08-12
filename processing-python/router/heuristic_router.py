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

class HeuristicRouter:
    """Applies transparent decision rules to select a model."""

    def route(self, inputs: RouterInputs, min_context_tokens: int) -> RoutingDecision:
        filtered, reason = self._filter_by_context(inputs.candidate_models, min_context_tokens, inputs)
        if not filtered:
            return RoutingDecision(model_id=None, reason=reason)

        filtered, reason = self._filter_by_latency(filtered, inputs.constraints)
        if not filtered:
            return RoutingDecision(model_id=None, reason=reason)

        if len(filtered) == 1:
            chosen = filtered[0]
        else:
            chosen = self._prefer_low_failure(filtered)

        return RoutingDecision(model_id=chosen.model_id, reason=f"Selected based on {chosen.annotations.get('reason', 'heuristics')}")

    def _filter_by_context(
        self, candidates: List[CandidateModel], min_context: int, inputs: RouterInputs
    ) -> tuple[List[CandidateModel], str]:
        eligible: List[CandidateModel] = []
        for candidate in candidates:
            capacity = candidate.profile.tasks.get(inputs.task_type.value).tokens if candidate.profile else None
            if capacity is None:
                eligible.append(candidate)
                candidate.annotations["reason"] = "no profile data; keeping candidate"
                continue
            if capacity >= max(min_context, inputs.document_features.token_estimate):
                eligible.append(candidate)
                candidate.annotations["reason"] = f"context capacity {capacity} ok"
            else:
                candidate.annotations["reason"] = f"context capacity {capacity} insufficient"
        reason = "Filtered by context capacity"
        return eligible, reason

    def _filter_by_latency(
        self, candidates: List[CandidateModel], constraints: Constraints
    ) -> tuple[List[CandidateModel], str]:
        if constraints.max_latency_ms is None:
            return candidates, "No latency constraint"
        eligible: List[CandidateModel] = []
        for candidate in candidates:
            latency = candidate.expected_latency_ms or (candidate.profile.tasks.get(candidate.annotations.get("task", "")) if candidate.profile else None)
            if latency is None or latency <= constraints.max_latency_ms:
                eligible.append(candidate)
                candidate.annotations["reason"] = candidate.annotations.get("reason", "") + "; latency ok"
            else:
                candidate.annotations["reason"] = candidate.annotations.get("reason", "") + "; latency exceeded"
        reason = "Filtered by latency constraint"
        return eligible, reason

    def _prefer_low_failure(self, candidates: List[CandidateModel]) -> CandidateModel:
        sorted_candidates = sorted(
            candidates,
            key=lambda c: (c.failure_rate if c.failure_rate is not None else 1.0, c.expected_latency_ms or float("inf")),
        )
        sorted_candidates[0].annotations["reason"] = sorted_candidates[0].annotations.get("reason", "") + "; lowest failure rate"
        return sorted_candidates[0]
