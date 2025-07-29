"""Data structures representing benchmark-derived model profiles."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class TaskProfile:
    latency_ms: float = 0.0
    tokens: float = 0.0
    error_rate: float = 0.0
    samples: int = 0

    def as_dict(self) -> Dict[str, float]:
        return {
            "latency_ms": self.latency_ms,
            "tokens": self.tokens,
            "error_rate": self.error_rate,
            "samples": self.samples,
        }


@dataclass
class ModelProfile:
    model_id: str
    tasks: Dict[str, TaskProfile] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, Dict[str, float]]:
        return {task: profile.as_dict() for task, profile in self.tasks.items()}
