from __future__ import annotations

import json

from twitch_moderator.analyzers.semantic_base import (
    SemanticAnalyzer,
    SemanticAnalyzerError,
    SemanticAnalyzerTimeoutError,
)
from twitch_moderator.models import SemanticAnalysisRequest, SemanticAnalysisResult
from twitch_moderator.prompting import render_semantic_prompt


class LLMStubAnalyzer(SemanticAnalyzer):
    def __init__(
        self,
        prompt_template: str,
        timeout_seconds: int = 5,
        retry_count: int = 0,
        stub_response: dict[str, object] | None = None,
        failure_sequence: list[Exception] | None = None,
    ) -> None:
        self._prompt_template = prompt_template
        self._timeout_seconds = timeout_seconds
        self._retry_count = retry_count
        self._stub_response = stub_response or {
            "toxicity": 0.0,
            "target": "none",
            "confidence": 1.0,
            "reason": "LLM stub default response",
        }
        self._failure_sequence = list(failure_sequence or [])
        self.attempt_count = 0

    @property
    def timeout_seconds(self) -> int:
        return self._timeout_seconds

    @property
    def retry_count(self) -> int:
        return self._retry_count

    def analyze(self, request: SemanticAnalysisRequest) -> SemanticAnalysisResult:
        last_error: SemanticAnalyzerError | None = None

        for _ in range(self._retry_count + 1):
            self.attempt_count += 1
            try:
                return self._attempt_analysis(request)
            except SemanticAnalyzerError as exc:
                last_error = exc

        if last_error is None:
            raise SemanticAnalyzerError("Semantic analyzer failed without a captured error")
        raise last_error

    def _attempt_analysis(self, request: SemanticAnalysisRequest) -> SemanticAnalysisResult:
        rendered_prompt = render_semantic_prompt(self._prompt_template, request)
        del rendered_prompt

        if self._failure_sequence:
            error = self._failure_sequence.pop(0)
            if isinstance(error, TimeoutError):
                raise SemanticAnalyzerTimeoutError(
                    f"Semantic analyzer timed out after {self._timeout_seconds} seconds"
                ) from error
            if isinstance(error, SemanticAnalyzerError):
                raise error
            raise SemanticAnalyzerError(str(error)) from error

        # Keep the same JSON boundary the real LLM integration will use.
        raw_json = json.dumps(self._stub_response)
        payload = json.loads(raw_json)
        try:
            return SemanticAnalysisResult.from_dict(payload)
        except ValueError as exc:
            raise SemanticAnalyzerError(f"Semantic analyzer returned invalid JSON payload: {exc}") from exc
