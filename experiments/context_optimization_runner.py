"""Experiment measuring token savings from section selection."""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSING_PATH = PROJECT_ROOT / "processing-python"
if str(PROCESSING_PATH) not in sys.path:
    sys.path.insert(0, str(PROCESSING_PATH))

from context.section_selector import SectionSelector  # type: ignore
from context.token_budget import Budget  # type: ignore
from context.token_estimator import estimate_tokens  # type: ignore
from router.task_types import TaskType  # type: ignore


def load_sections() -> list:
    return [
        {
            "title": "Management Discussion",
            "paragraphs": [
                "Revenue increased by 12% year over year.",
                "Operating expenses were flat compared to Q3.",
            ],
        },
        {
            "title": "Risk Factors",
            "paragraphs": [
                "Supply chain constraints may impact delivery schedules.",
            ],
        },
    ]


def run_experiment(output_path: str) -> None:
    budget = Budget(max_input_tokens=2000, max_output_tokens=512, safety_margin=0.1)
    selector = SectionSelector(budget=budget)
    sections = load_sections()

    normalized = [type("Section", (), section) for section in sections]
    token_before = estimate_tokens("\n".join("\n".join(section["paragraphs"]) for section in sections))

    selection = selector.select(normalized, TaskType.EXTRACTION)
    token_after = sum(item.token_estimate for item in selection)

    results = {
        "token_before": token_before,
        "token_after": token_after,
        "selected_sections": [item.section.title for item in selection],
        "selection_reasons": [item.reason for item in selection],
    }

    Path(output_path).write_text(json.dumps(results, indent=2), encoding="utf-8")


if __name__ == "__main__":
    run_experiment("experiments/context_optimization_results.json")
