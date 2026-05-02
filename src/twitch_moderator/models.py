from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class ChatMessage:
    username: str
    message: str


@dataclass(frozen=True)
class SemanticAnalysisRequest:
    current_message: ChatMessage
    context: list[ChatMessage]
    streamer_identity: list[str]
    custom_rules: list[str]

    def to_dict(self) -> dict[str, object]:
        return {
            "current_message": {
                "username": self.current_message.username,
                "message": self.current_message.message,
            },
            "context": [
                {
                    "username": message.username,
                    "message": message.message,
                }
                for message in self.context
            ],
            "streamer_identity": list(self.streamer_identity),
            "custom_rules": list(self.custom_rules),
        }


@dataclass(frozen=True)
class AnalysisResult:
    is_toxic: bool
    confidence: float
    reason: str


SemanticTarget = Literal["streamer", "chatter", "game", "external", "none"]


@dataclass(frozen=True)
class SemanticAnalysisResult:
    toxicity: float
    target: SemanticTarget
    confidence: float
    reason: str

    def __post_init__(self) -> None:
        _validate_score("toxicity", self.toxicity)
        _validate_score("confidence", self.confidence)
        _validate_target(self.target)

    def to_dict(self) -> dict[str, object]:
        return {
            "toxicity": self.toxicity,
            "target": self.target,
            "confidence": self.confidence,
            "reason": self.reason,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "SemanticAnalysisResult":
        return cls(
            toxicity=_require_float(payload, "toxicity"),
            target=_require_target(payload, "target"),
            confidence=_require_float(payload, "confidence"),
            reason=_require_string(payload, "reason"),
        )


@dataclass(frozen=True)
class ModerationDecision:
    should_timeout: bool
    reason: str

    def to_dict(self) -> dict[str, object]:
        return {
            "should_timeout": self.should_timeout,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class ModerationAction:
    username: str
    reason: str
    duration_seconds: int


_VALID_TARGETS = {"streamer", "chatter", "game", "external", "none"}


def _validate_score(name: str, value: float) -> None:
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be between 0.0 and 1.0")


def _validate_target(value: str) -> None:
    if value not in _VALID_TARGETS:
        raise ValueError(f"target must be one of: {', '.join(sorted(_VALID_TARGETS))}")


def _require_float(payload: dict[str, object], key: str) -> float:
    if key not in payload:
        raise ValueError(f"Missing required field: {key}")

    value = payload[key]
    if not isinstance(value, (int, float)):
        raise ValueError(f"{key} must be a number")

    return float(value)


def _require_string(payload: dict[str, object], key: str) -> str:
    if key not in payload:
        raise ValueError(f"Missing required field: {key}")

    value = payload[key]
    if not isinstance(value, str):
        raise ValueError(f"{key} must be a string")

    return value


def _require_target(payload: dict[str, object], key: str) -> SemanticTarget:
    target = _require_string(payload, key)
    _validate_target(target)
    return target
