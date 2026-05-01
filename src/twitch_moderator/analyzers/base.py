from __future__ import annotations

from abc import ABC, abstractmethod

from twitch_moderator.models import AnalysisResult, ChatMessage


class Analyzer(ABC):
    @abstractmethod
    def analyze(self, current_message: ChatMessage, context: list[ChatMessage]) -> AnalysisResult:
        raise NotImplementedError

