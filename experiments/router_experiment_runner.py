"""Experimental harness to evaluate heuristic routing decisions."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import List

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSING_PATH = PROJECT_ROOT / "processing-python"
if str(PROCESSING_PATH) not in sys.path:
    sys.path.insert(0, str(PROCESSING_PATH))

from features.document_features import DocumentFeatures  # type: ignore
from router.heuristic_router import HeuristicRouter  # type: ignore
from router.router_inputs import CandidateModel, Constraints, RouterInputs  # type: ignore
from router.router_logger import RouterLogger  # type: ignore
from router.task_types import TaskType  # type: ignore
from benchmarks.model_profile import ModelProfile, TaskProfile  # type: ignore

def load_document_features(path: str) -> List[DocumentFeatures]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    features = []
    for entry in payload:
        features.append(
            DocumentFeatures(
                language=entry["document_features"].get("language"),
                character_count=entry["document_features"].get("character_count", 0),
                token_estimate=entry["document_features"].get("token_estimate", 0),
                sections=entry["document_features"].get("sections", 0),
                financial_terms=entry["document_features"].get("financial_terms", False),
            )
        )
    return features

def fake_model_profiles() -> List[CandidateModel]:
    small_profile = ModelProfile(
        model_id="local-llm-small",
        tasks={
            "classification": TaskProfile(latency_ms=300, tokens=3000, error_rate=0.02),
            "extraction": TaskProfile(latency_ms=2300, tokens=9200, error_rate=0.05),
        },
    )
    large_profile = ModelProfile(
        model_id="local-llm-large",
        tasks={
            "classification": TaskProfile(latency_ms=600, tokens=12000, error_rate=0.01),
            "extraction": TaskProfile(latency_ms=2000, tokens=15000, error_rate=0.08),
        },
    )
    return [
        CandidateModel(model_id="local-llm-small", profile=small_profile, expected_latency_ms=300, failure_rate=0.02),
        CandidateModel(model_id="local-llm-large", profile=large_profile, expected_latency_ms=600, failure_rate=0.08),
    ]

