"""Lightweight pipeline orchestrator tying together processing-llm stages."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum, auto
from typing import Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class PipelineStatus(Enum):
    COLLECTED = auto()
    PREPROCESSED = auto()
    ROUTED = auto()
    BATCHED = auto()
    INFERRED = auto()
    VALIDATED = auto()


@dataclass
class PipelineState:
    document_id: str
    status: PipelineStatus
    metadata: Dict[str, object]


class PipelineOrchestrator:
    """Executes pipeline stages sequentially with logging and status tracking."""

    def __init__(
        self,
        collectors: Dict[str, Callable[[PipelineState], PipelineState]],
        preprocessors: Dict[str, Callable[[PipelineState], PipelineState]],
        router: Callable[[PipelineState], PipelineState],
        batcher: Callable[[PipelineState], PipelineState],
        inference_runner: Callable[[PipelineState], PipelineState],
        validator: Callable[[PipelineState], PipelineState],
    ) -> None:
        self.collectors = collectors
        self.preprocessors = preprocessors
        self.router = router
        self.batcher = batcher
        self.inference_runner = inference_runner
        self.validator = validator

    def run(self, document_id: str, source_type: str, preprocess_variant: str) -> PipelineState:
        state = PipelineState(document_id=document_id, status=PipelineStatus.COLLECTED, metadata={})
        logger.info("Starting pipeline for %s at status %s", document_id, state.status.name)

        collector = self.collectors.get(source_type)
        if not collector:
            raise ValueError(f"No collector registered for {source_type}")
        state = collector(state)
        state.status = PipelineStatus.PREPROCESSED
        logger.info("Collector completed for %s -> %s", document_id, state.status.name)

        preprocessor = self.preprocessors.get(preprocess_variant)
        if not preprocessor:
            raise ValueError(f"No preprocessor variant {preprocess_variant}")
        state = preprocessor(state)

        state = self._advance(state, PipelineStatus.ROUTED, self.router)
        state = self._advance(state, PipelineStatus.BATCHED, self.batcher)
        state = self._advance(state, PipelineStatus.INFERRED, self.inference_runner)
        state = self._advance(state, PipelineStatus.VALIDATED, self.validator)

        logger.info("Pipeline completed for %s at status %s", document_id, state.status.name)
        return state

    def _advance(
        self,
        state: PipelineState,
        next_status: PipelineStatus,
        step: Callable[[PipelineState], PipelineState],
    ) -> PipelineState:
        logger.info("Running step %s for %s", next_status.name, state.document_id)
        updated_state = step(state)
        updated_state.status = next_status
        logger.info("Step %s completed for %s", next_status.name, state.document_id)
        return updated_state
