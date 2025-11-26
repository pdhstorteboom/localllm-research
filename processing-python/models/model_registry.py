"""Central registry defining default OpenRouter models per task."""

from __future__ import annotations

import os
from typing import Dict, Mapping

from router.task_types import TaskType


_FALLBACK_MODEL = os.getenv("OPENROUTER_MODEL_DEFAULT", "openai/gpt-4o-mini")
_TASK_MODELS: Dict[TaskType, str] = {
    TaskType.CLASSIFICATION: os.getenv("OPENROUTER_MODEL_CLASSIFICATION", "google/gemini-pro"),
    TaskType.EXTRACTION: os.getenv("OPENROUTER_MODEL_EXTRACTION", "anthropic/claude-3.5-sonnet"),
    TaskType.RAG: os.getenv("OPENROUTER_MODEL_RAG", "perplexity/sonar-medium-online"),
    TaskType.SUMMARIZATION: os.getenv("OPENROUTER_MODEL_SUMMARIZATION", _FALLBACK_MODEL),
}


def default_model_for_task(task_type: TaskType) -> str:
    """Return the preferred model for a task, falling back to a shared default."""
    return _TASK_MODELS.get(task_type, _FALLBACK_MODEL)


def register_model(task_type: TaskType, model_id: str) -> None:
    """Override the model associated with a task at runtime."""
    _TASK_MODELS[task_type] = model_id


def available_task_models() -> Mapping[TaskType, str]:
    """Expose a copy of the configured task models."""
    return dict(_TASK_MODELS)
