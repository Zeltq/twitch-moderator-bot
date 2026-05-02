from __future__ import annotations

from abc import ABC, abstractmethod

from twitch_moderator.models import SemanticAnalysisRequest, SemanticAnalysisResult


class SemanticAnalyzerError(RuntimeError):
    pass


class SemanticAnalyzerTimeoutError(SemanticAnalyzerError):
    pass


class SemanticAnalyzer(ABC):
    @abstractmethod
    def analyze(self, request: SemanticAnalysisRequest) -> SemanticAnalysisResult:
        raise NotImplementedError
