"""Task queue supporting batching for local LLM execution."""

from __future__ import annotations

import heapq
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Optional

from batching.task import LlmTask
from router.task_types import TaskType


class TaskQueue:
    """Priority-aware task queue with simple batching."""

    def __init__(self) -> None:
        self._heap: List[LlmTask] = []

    def add_task(self, task: LlmTask) -> None:
        if task.deadline is None:
            task.deadline = datetime.max
        heapq.heappush(self._heap, task)

    def pop_next_batch(self, batch_size: int, task_type: Optional[TaskType] = None) -> List[LlmTask]:
        if not self._heap:
            return []
        batch: List[LlmTask] = []
        buffer: List[LlmTask] = []

        while self._heap and len(batch) < batch_size:
            candidate = heapq.heappop(self._heap)
            if task_type and candidate.task_type != task_type:
                buffer.append(candidate)
                continue
            
