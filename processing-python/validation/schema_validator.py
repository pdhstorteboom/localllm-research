"""Schema validation for LLM output."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, List

from jsonschema import Draft7Validator  # type: ignore


@dataclass
class ValidationIssue:
    message: str
    path: str
    issue_type: str


@dataclass
class ValidationResult:
    valid: bool
    issues: List[ValidationIssue]


class SchemaValidator:
    def __init__(self, schema_path: str) -> None:
        with open(schema_path, "r", encoding="utf-8") as handle:
            schema = json.load(handle)
        self.validator = Draft7Validator(schema)

    def validate(self, payload: Any) -> ValidationResult:
        issues: List[ValidationIssue] = []
        for error in self.validator.iter_errors(payload):
            issue_type = self._classify_error(error)
            issues.append(
                ValidationIssue(
                    message=error.message,
                    path=".".join(str(p) for p in error.absolute_path),
                    issue_type=issue_type,
                )
            )
        return ValidationResult(valid=len(issues) == 0, issues=issues)

    def _classify_error(self, error) -> str:
        if error.validator == "required":
            return "missing_field"
        if error.validator == "type":
            return "type_mismatch"
        if error.validator == "enum":
            return "enum_mismatch"
        return "validation_error"
