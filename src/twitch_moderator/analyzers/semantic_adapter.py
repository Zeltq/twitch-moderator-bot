from __future__ import annotations

from twitch_moderator.analyzers.base import Analyzer
from twitch_moderator.analyzers.semantic_base import SemanticAnalyzer
from twitch_moderator.models import AnalysisResult, ChatMessage, SemanticAnalysisRequest


class SemanticAnalyzerAdapter(Analyzer):
    def __init__(
        self,
        semantic_analyzer: SemanticAnalyzer,
        streamer_identity: list[str],
        custom_rules: list[str] | None = None,
    ) -> None:
        self._semantic_analyzer = semantic_analyzer
        self._streamer_identity = list(streamer_identity)
        self._custom_rules = list(custom_rules or [])

    def analyze(self, current_message: ChatMessage, context: list[ChatMessage]) -> AnalysisResult:
        request = SemanticAnalysisRequest(
            current_message=current_message,
            context=context,
            streamer_identity=list(self._streamer_identity),
            custom_rules=list(self._custom_rules),
        )
        result = self._semantic_analyzer.analyze(request)
        return AnalysisResult(
            is_toxic=result.toxicity > 0.0,
            confidence=result.confidence,
            reason=result.reason,
        )
