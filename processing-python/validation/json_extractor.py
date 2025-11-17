"""Utility to extract JSON payloads from noisy LLM outputs."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, List, Tuple


class JsonExtractionError(Exception):
    """Raised when JSON cannot be extracted."""

    def __init__(self, message: str, error_type: str) -> None:
        super().__init__(message)
        self.error_type = error_type


FENCE_PATTERN = re.compile(r"```(?:json)?(.*?)```", re.DOTALL | re.IGNORECASE)
JSON_PATTERN = re.compile(r"\{.*\}", re.DOTALL)


@dataclass
class ExtractionResult:
    content: Any
    raw: str


class JsonExtractor:
    """Attempts to extract valid JSON even when surrounding noise exists."""

    def extract(self, text: str) -> ExtractionResult:
        candidates = self._find_candidates(text)
        errors: List[Tuple[str, str]] = []
        for raw in candidates:
            try:
                return ExtractionResult(content=json.loads(raw), raw=raw)
            except json.JSONDecodeError as exc:
                errors.append((raw, f"decode_error:{exc.msg}"))

        error_type = errors[0][1] if errors else "no_json_candidate"
        raise JsonExtractionError("Failed to extract JSON", error_type)

    def _find_candidates(self, text: str) -> List[str]:
        candidates: List[str] = []

        for match in FENCE_PATTERN.finditer(text):
            candidates.append(match.group(1).strip())
        if candidates:
            return candidates

        stripped = text.strip()
        if stripped.startswith("{") and stripped.endswith("}"):
            candidates.append(stripped)

        for match in JSON_PATTERN.finditer(text):
            candidates.append(match.group(0))

        return candidates
