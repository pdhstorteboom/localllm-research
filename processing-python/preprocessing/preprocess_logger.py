"""Utilities for logging preprocessing metrics for WBSO experiments."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, List, Optional

from preprocessing.cleaner import NormalizedSection
from features.document_features import DocumentFeatures


@dataclass
class PreprocessRecord:
    document_id: str
    original_length: int
    cleaned_length: int
    token_estimate: int
    sections: int
    language: Optional[str]
    financial_terms: bool
    errors: List[str]


