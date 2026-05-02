from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from twitch_moderator.models import SemanticTarget


@dataclass(frozen=True)
class MetricsSnapshot:
    total_messages: int
    average_toxicity: float
    timeout_count: int
    target_distribution: dict[str, int]


class RuntimeMetrics:
    def __init__(self, log_every_messages: int = 10) -> None:
        if log_every_messages <= 0:
            raise ValueError("log_every_messages must be greater than zero")

        self._log_every_messages = log_every_messages
        self._total_messages = 0
        self._toxicity_sum = 0.0
        self._timeout_count = 0
        self._target_counts: Counter[str] = Counter()

    def record_message(self, toxicity: float, target: SemanticTarget | None, timed_out: bool) -> None:
        self._total_messages += 1
        self._toxicity_sum += toxicity
        if timed_out:
            self._timeout_count += 1
        if target is not None:
            self._target_counts[target] += 1

    def should_log_snapshot(self) -> bool:
        return self._total_messages > 0 and self._total_messages % self._log_every_messages == 0

    def snapshot(self) -> MetricsSnapshot:
        average_toxicity = 0.0
        if self._total_messages > 0:
            average_toxicity = self._toxicity_sum / self._total_messages

        return MetricsSnapshot(
            total_messages=self._total_messages,
            average_toxicity=average_toxicity,
            timeout_count=self._timeout_count,
            target_distribution=dict(self._target_counts),
        )
