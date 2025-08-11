"""Enumerations for router task semantics."""

from __future__ import annotations

from enum import Enum


class TaskType(str, Enum):
    """Canonical task identifiers for routing decisions."""

    CLASSIFICATION = "classification"
    EXTRACTION = "extraction"
    SUMMARIZATION = "summarization"
