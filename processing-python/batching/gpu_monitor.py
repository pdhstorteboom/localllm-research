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


class GpuMonitor:
    """Wrap nvidia-smi when available; fallback to empty stats otherwise."""

    def __init__(self) -> None:
        self.nvidia_smi = shutil.which("nvidia-smi")

    def sample(self) -> List[GpuStatus]:
        if not self.nvidia_smi:
            return []
        query = [
            self.nvidia_smi,
            "--query-gpu=index,name,memory.total,memory.used,memory.free",
            "--format=csv,noheader,nounits",
        ]
        gpu_output = self._run(query)
        status = self._parse_gpu_output(gpu_output)

        process_query = [
            self.nvidia_smi,
            "--query-compute-apps=gpu_uuid,pid,process_name,used_memory",
            "--format=csv,noheader,nounits",
        ]
        process_output = self._run(process_query)
        self._attach_processes(status, process_output)
        return status

    def _run(self, command: List[str]) -> str:
        try:
            return subprocess.check_output(command, text=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            return ""

    def _parse_gpu_output(self, output: str) -> List[GpuStatus]:
        status: List[GpuStatus] = []
        for line in output.strip().splitlines():
            parts = [p.strip() for p in line.split(",")]
            if len(parts) != 5:
                continue
            index, name, total, used, free = parts
            status.append(
                GpuStatus(
                    index=int(index),
                    name=name,
                    total_memory_mb=int(total),
                    used_memory_mb=int(used),
                    free_memory_mb=int(free),
                    processes=[],
                )
            )
        return status

    def _attach_processes(self, status: List[GpuStatus], output: str) -> None:
        for line in output.strip().splitlines():
            parts = [p.strip() for p in line.split(",")]
            if len(parts) != 4:
                continue
            gpu_uuid, pid, name, memory = parts
            process = GpuProcess(pid=int(pid), name=name, memory_mb=int(memory))
            if status:
                status[0].processes.append(process)
