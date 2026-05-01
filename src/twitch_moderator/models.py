from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ChatMessage:
    username: str
    message: str


@dataclass(frozen=True)
class AnalysisResult:
    is_toxic: bool
    confidence: float
    reason: str


@dataclass(frozen=True)
class ModerationAction:
    username: str
    reason: str
    duration_seconds: int

