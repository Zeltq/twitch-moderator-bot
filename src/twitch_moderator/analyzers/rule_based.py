from __future__ import annotations

import re

from twitch_moderator.analyzers.base import Analyzer
from twitch_moderator.models import AnalysisResult, ChatMessage


class RuleBasedAnalyzer(Analyzer):
    def __init__(self, blacklist: list[str] | tuple[str, ...], min_matches: int = 1) -> None:
        if min_matches <= 0:
            raise ValueError("min_matches must be greater than zero")

        self._blacklist = tuple(word.casefold() for word in blacklist if word.strip())
        self._min_matches = min_matches

    def analyze(self, current_message: ChatMessage, context: list[ChatMessage]) -> AnalysisResult:
        del context

        normalized_message = _normalize_text(current_message.message)
        matches = [word for word in self._blacklist if word in normalized_message]

        if len(matches) >= self._min_matches:
            return AnalysisResult(
                is_toxic=True,
                confidence=1.0,
                reason=f"Matched blacklist: {', '.join(matches)}",
            )

        return AnalysisResult(
            is_toxic=False,
            confidence=0.0,
            reason="No blacklist matches",
        )


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.casefold()).strip()

