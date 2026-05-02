from __future__ import annotations

from dataclasses import dataclass

from twitch_moderator.models import ModerationDecision, SemanticAnalysisResult


@dataclass(frozen=True)
class DecisionPolicy:
    streamer_threshold: float
    chatter_threshold: float
    none_threshold: float
    min_confidence: float


class DecisionEngine:
    def __init__(self, policy: DecisionPolicy) -> None:
        self._policy = policy

    def decide(self, result: SemanticAnalysisResult) -> ModerationDecision:
        if result.confidence < self._policy.min_confidence:
            return ModerationDecision(
                should_timeout=False,
                reason="Confidence below minimum threshold",
            )

        if result.target == "game":
            return ModerationDecision(
                should_timeout=False,
                reason="Ignored target: game",
            )

        if result.target == "external":
            return ModerationDecision(
                should_timeout=False,
                reason="Ignored target: external",
            )

        if result.target == "streamer":
            return self._threshold_decision(
                result=result,
                threshold=self._policy.streamer_threshold,
                matched_reason="Streamer toxicity threshold exceeded",
                rejected_reason="Streamer toxicity below threshold",
            )

        if result.target == "chatter":
            return self._threshold_decision(
                result=result,
                threshold=self._policy.chatter_threshold,
                matched_reason="Chatter toxicity threshold exceeded",
                rejected_reason="Chatter toxicity below threshold",
            )

        if result.target == "none":
            return self._threshold_decision(
                result=result,
                threshold=self._policy.none_threshold,
                matched_reason="Unspecified target toxicity threshold exceeded",
                rejected_reason="Unspecified target toxicity below threshold",
            )

        return ModerationDecision(
            should_timeout=False,
            reason="Unhandled target",
        )

    def _threshold_decision(
        self,
        result: SemanticAnalysisResult,
        threshold: float,
        matched_reason: str,
        rejected_reason: str,
    ) -> ModerationDecision:
        if result.toxicity >= threshold:
            return ModerationDecision(
                should_timeout=True,
                reason=matched_reason,
            )

        return ModerationDecision(
            should_timeout=False,
            reason=rejected_reason,
        )
