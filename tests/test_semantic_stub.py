import unittest

from twitch_moderator.analyzers.semantic_base import SemanticAnalyzerError, SemanticAnalyzerTimeoutError
from twitch_moderator.analyzers.semantic_adapter import SemanticAnalyzerAdapter
from twitch_moderator.analyzers.semantic_stub import LLMStubAnalyzer
from twitch_moderator.models import ChatMessage, SemanticAnalysisRequest


class LLMStubAnalyzerTests(unittest.TestCase):
    def test_stub_analyzer_returns_semantic_contract(self) -> None:
        analyzer = LLMStubAnalyzer(
            prompt_template="Streamer:\n{streamer_identity}\nMessage: {current_message}",
            timeout_seconds=7,
            retry_count=2,
            stub_response={
                "toxicity": 0.75,
                "target": "streamer",
                "confidence": 0.9,
                "reason": "Stub semantic result",
            },
        )

        result = analyzer.analyze(
            SemanticAnalysisRequest(
                current_message=ChatMessage(username="user1", message="you are bad"),
                context=[],
                streamer_identity=["zeltq", "Leha"],
                custom_rules=[],
            )
        )

        self.assertEqual(result.toxicity, 0.75)
        self.assertEqual(result.target, "streamer")
        self.assertEqual(result.confidence, 0.9)
        self.assertEqual(result.reason, "Stub semantic result")
        self.assertEqual(analyzer.timeout_seconds, 7)
        self.assertEqual(analyzer.retry_count, 2)
        self.assertEqual(analyzer.attempt_count, 1)

    def test_stub_analyzer_retries_and_recovers_after_timeout(self) -> None:
        analyzer = LLMStubAnalyzer(
            prompt_template="Message: {current_message}",
            timeout_seconds=3,
            retry_count=2,
            stub_response={
                "toxicity": 0.5,
                "target": "none",
                "confidence": 0.7,
                "reason": "Recovered after retry",
            },
            failure_sequence=[TimeoutError("simulated timeout")],
        )

        result = analyzer.analyze(
            SemanticAnalysisRequest(
                current_message=ChatMessage(username="user1", message="hello"),
                context=[],
                streamer_identity=["zeltq"],
                custom_rules=[],
            )
        )

        self.assertEqual(result.reason, "Recovered after retry")
        self.assertEqual(analyzer.attempt_count, 2)

    def test_stub_analyzer_exhausts_retries_on_timeout(self) -> None:
        analyzer = LLMStubAnalyzer(
            prompt_template="Message: {current_message}",
            timeout_seconds=2,
            retry_count=1,
            failure_sequence=[TimeoutError("t1"), TimeoutError("t2")],
        )

        with self.assertRaisesRegex(SemanticAnalyzerTimeoutError, "timed out after 2 seconds"):
            analyzer.analyze(
                SemanticAnalysisRequest(
                    current_message=ChatMessage(username="user1", message="hello"),
                    context=[],
                    streamer_identity=["zeltq"],
                    custom_rules=[],
                )
            )

        self.assertEqual(analyzer.attempt_count, 2)

    def test_stub_analyzer_raises_semantic_error_on_invalid_payload(self) -> None:
        analyzer = LLMStubAnalyzer(
            prompt_template="Message: {current_message}",
            stub_response={
                "toxicity": "bad",
                "target": "streamer",
                "confidence": 0.5,
                "reason": "invalid payload",
            },
        )

        with self.assertRaisesRegex(SemanticAnalyzerError, "invalid JSON payload"):
            analyzer.analyze(
                SemanticAnalysisRequest(
                    current_message=ChatMessage(username="user1", message="hello"),
                    context=[],
                    streamer_identity=["zeltq"],
                    custom_rules=[],
                )
            )

    def test_semantic_adapter_keeps_main_flow_compatible(self) -> None:
        semantic_analyzer = LLMStubAnalyzer(
            prompt_template="Message: {current_message}",
            stub_response={
                "toxicity": 0.6,
                "target": "chatter",
                "confidence": 0.8,
                "reason": "Semantic adapter result",
            },
        )
        adapter = SemanticAnalyzerAdapter(
            semantic_analyzer=semantic_analyzer,
            streamer_identity=["zeltq", "Leha"],
            custom_rules=[],
        )

        result = adapter.analyze(ChatMessage(username="user1", message="possible toxicity"), context=[])

        self.assertTrue(result.is_toxic)
        self.assertEqual(result.confidence, 0.8)
        self.assertEqual(result.reason, "Semantic adapter result")


if __name__ == "__main__":
    unittest.main()
