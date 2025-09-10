"""GPU monitoring utilities for local resource management."""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class GpuProcess:
    pid: int
    name: str
    memory_mb: int


@dataclass
class GpuStatus:
    index: int
    name: str
    total_memory_mb: int
    used_memory_mb: int
    free_memory_mb: int
    processes: List[GpuProcess]