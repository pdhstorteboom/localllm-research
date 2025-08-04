"""Aggregate benchmark results into per-model profiles."""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, Iterable

from benchmarks.model_profile import ModelProfile, TaskProfile
from benchmarks.result_writer import BenchmarkResult


class ProfileAggregator:
    """Combines benchmark outputs into aggregated model profiles."""

    def aggregate(self, results: Iterable[BenchmarkResult]) -> Dict[str, ModelProfile]:
        grouped: Dict[str, ModelProfile] = {}
        stats = defaultdict(lambda: defaultdict(list))

        for result in results:
            stats[result.model_id][result.task_type].append(result)

        for model_id, tasks in stats.items():
            profile = ModelProfile(model_id=model_id)
            for task_type, task_results in tasks.items():
                profile.tasks[task_type] = self._summarize(task_results)
            grouped[model_id] = profile

        return grouped

    @staticmethod
    def _summarize(results: Iterable[BenchmarkResult]) -> TaskProfile:
        results_list = list(results)
        total_latency = sum(r.duration_ms() for r in results_list)
        total_tokens = sum(r.input_tokens + r.output_tokens for r in results_list)
        error_count = sum(1 for r in results_list if r.error)
        samples = len(results_list)

        if samples == 0:
            return TaskProfile()

        return TaskProfile(
            latency_ms=total_latency / samples,
            tokens=total_tokens / samples,
            error_rate=error_count / samples,
            samples=samples,
        )
