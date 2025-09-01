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