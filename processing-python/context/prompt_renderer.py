"""Prompt template rendering for model-specific formats."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

from context.section_selector import SelectionResult
from router.task_types import TaskType


@dataclass
class PromptContext:
    sections: List[SelectionResult]
    schema_reference: str
    model_format: str  # "chat" or "instruct"


class PromptRenderer:
    """Renders prompts based on templates and selected sections."""

    TEMPLATE_MAP = {
        TaskType.EXTRACTION: "prompts/task_extract_entities.txt",
        TaskType.CLASSIFICATION: "prompts/task_classification.txt",
        TaskType.RAG: "prompts/task_rag.txt",
    }

    def __init__(self, system_prompt_path: str = "prompts/base_system_prompt.txt") -> None:
        self.system_prompt = Path(system_prompt_path).read_text(encoding="utf-8")

    def render(self, task_type: TaskType, context: PromptContext) -> str:
        template_path = self.TEMPLATE_MAP.get(task_type)
        if not template_path:
            raise ValueError(f"No template for task {task_type}")
        template = Path(template_path).read_text(encoding="utf-8")
        context_text = "\n\n".join(section.section.title or "untitled" + ":\n" + "\n".join(section.section.paragraphs) for section in context.sections)

        prompt_body = template.replace("{{context}}", context_text)
        prompt_body = prompt_body.replace("{{schema_reference}}", context.schema_reference)

        if context.model_format == "chat":
            return self._render_chat(prompt_body)
        return self._render_instruct(prompt_body)

    def _render_chat(self, prompt_body: str) -> str:
        return f"{self.system_prompt}\n\nUser:\n{prompt_body}\n\nAssistant:"

    def _render_instruct(self, prompt_body: str) -> str:
        return f"{self.system_prompt}\n\n{prompt_body}"
