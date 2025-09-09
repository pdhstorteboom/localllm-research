"""Data models representing scheduled LLM tasks."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from router.task_types import TaskType


@dataclass
class TaskConstraints:
    """Optional constraints such as fixed model or resource caps."""

    preferred_model: Optional[str] = None
    max_tokens: Optional[int] = None
    gpu_required: bool = False


@dataclass(order=True)
class LlmTask:
    """Individual work unit queued for batching."""

    priority: int
    deadline: Optional[datetime] = field(compare=False, default=None)
    task_id: str = field(compare=False, default="")
    doc_id: str = field(compare=False, default="")
    task_type: TaskType = field(compare=False, default=TaskType.EXTRACTION)
    target_model: Optional[str] = field(compare=False, default=None)
    token_estimate: int = field(compare=False, default=0)
    constraints: TaskConstraints = field(compare=False, default_factory=TaskConstraints)
