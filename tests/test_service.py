import unittest

from twitch_moderator.analyzers.base import Analyzer
from twitch_moderator.analyzers.semantic_base import SemanticAnalyzer, SemanticAnalyzerError
from twitch_moderator.buffer import MessageBuffer
from twitch_moderator.config import AppConfig
from twitch_moderator.metrics import RuntimeMetrics
from twitch_moderator.models import AnalysisResult, ChatMessage, ModerationDecision, SemanticAnalysisRequest, SemanticAnalysisResult
from twitch_moderator.service import ModerationService
from twitch_moderator.twitch_api import TwitchAPIError


class StubRuleBasedAnalyzer(Analyzer):
    def __init__(self, result: AnalysisResult) -> None:
        self._result = result
        self.last_context = None
        self.call_count = 0

    def analyze(self, current_message: ChatMessage, context: list[ChatMessage]) -> AnalysisResult:
        self.call_count += 1
        self.last_context = context
        return self._result


class StubSemanticAnalyzer(SemanticAnalyzer):
    def __init__(self, result: SemanticAnalysisResult) -> None:
        self._result = result
        self.last_request = None
        self.call_count = 0

    def analyze(self, request: SemanticAnalysisRequest) -> SemanticAnalysisResult:
        self.call_count += 1
        self.last_request = request
        return self._result


class StubDecisionEngine:
    def __init__(self, decision: ModerationDecision) -> None:
        self._decision = decision
        self.last_result = None
        self.call_count = 0

    def decide(self, result: SemanticAnalysisResult) -> ModerationDecision:
        self.call_count += 1
        self.last_result = result
        return self._decision


class FailingSemanticAnalyzer(SemanticAnalyzer):
    def __init__(self, error: Exception) -> None:
        self._error = error
        self.call_count = 0

    def analyze(self, request: SemanticAnalysisRequest) -> SemanticAnalysisResult:
        self.call_count += 1
        raise self._error


class StubExecutor:
    def __init__(self) -> None:
        self.actions = []

    def execute(self, action) -> None:
        self.actions.append(action)


class FailingExecutor:
    def __init__(self) -> None:
        self.actions = []

    def execute(self, action) -> None:
        self.actions.append(action)
        raise TwitchAPIError("Twitch API request failed 400: test error")


class ModerationServiceTests(unittest.TestCase):
    def test_service_uses_only_previous_messages_as_context(self) -> None:
        analyzer = StubRuleBasedAnalyzer(AnalysisResult(is_toxic=False, confidence=0.0, reason="ok"))
        executor = StubExecutor()
        config = AppConfig(channel="channel", bot_username="bot", oauth_token="oauth:test")
        service = ModerationService(analyzer, MessageBuffer(10), executor, config)

        service.handle_message(ChatMessage(username="user1", message="first"))
        service.handle_message(ChatMessage(username="user2", message="second"))

        self.assertEqual(analyzer.last_context, [ChatMessage(username="user1", message="first")])
        self.assertEqual(executor.actions, [])

    def test_service_executes_timeout_for_rule_based_matches(self) -> None:
        analyzer = StubRuleBasedAnalyzer(AnalysisResult(is_toxic=True, confidence=1.0, reason="Matched blacklist"))
        executor = StubExecutor()
        config = AppConfig(channel="channel", bot_username="bot", oauth_token="oauth:test", timeout_duration=42)
        service = ModerationService(analyzer, MessageBuffer(10), executor, config)

        service.handle_message(ChatMessage(username="user1", message="spam"))

        self.assertEqual(len(executor.actions), 1)
        self.assertEqual(executor.actions[0].username, "user1")
        self.assertEqual(executor.actions[0].duration_seconds, 42)

    def test_service_logs_and_continues_when_timeout_fails(self) -> None:
        analyzer = StubRuleBasedAnalyzer(AnalysisResult(is_toxic=True, confidence=1.0, reason="Matched blacklist: spam"))
        executor = FailingExecutor()
        buffer = MessageBuffer(10)
        config = AppConfig(channel="channel", bot_username="bot", oauth_token="oauth:test", timeout_duration=42)
        service = ModerationService(analyzer, buffer, executor, config)

        with self.assertLogs("twitch_moderator.service", level="WARNING") as logs:
            service.handle_message(ChatMessage(username="user1", message="spam"))

        self.assertEqual(len(executor.actions), 1)
        self.assertEqual(buffer.snapshot(), [ChatMessage(username="user1", message="spam")])
        self.assertTrue(any("Moderation action rejected" in entry for entry in logs.output))

    def test_service_does_not_call_semantic_analyzer_when_blacklist_matches(self) -> None:
        rule_based_analyzer = StubRuleBasedAnalyzer(AnalysisResult(is_toxic=True, confidence=1.0, reason="Matched blacklist"))
        semantic_analyzer = StubSemanticAnalyzer(
            SemanticAnalysisResult(
                toxicity=0.9,
                target="streamer",
                confidence=0.9,
                reason="semantic toxic",
            )
        )
        decision_engine = StubDecisionEngine(
            ModerationDecision(should_timeout=True, reason="semantic timeout")
        )
        executor = StubExecutor()
        config = AppConfig(channel="channel", bot_username="bot", oauth_token="oauth:test", timeout_duration=42)
        service = ModerationService(
            rule_based_analyzer,
            MessageBuffer(10),
            executor,
            config,
            semantic_analyzer=semantic_analyzer,
            decision_engine=decision_engine,
        )

        service.handle_message(ChatMessage(username="user1", message="spam"))

        self.assertEqual(rule_based_analyzer.call_count, 1)
        self.assertEqual(semantic_analyzer.call_count, 0)
        self.assertEqual(decision_engine.call_count, 0)
        self.assertEqual(len(executor.actions), 1)

    def test_service_calls_semantic_analyzer_and_decision_engine_when_blacklist_does_not_match(self) -> None:
        rule_based_analyzer = StubRuleBasedAnalyzer(AnalysisResult(is_toxic=False, confidence=0.0, reason="No blacklist matches"))
        semantic_analyzer = StubSemanticAnalyzer(
            SemanticAnalysisResult(
                toxicity=0.8,
                target="chatter",
                confidence=0.8,
                reason="semantic toxic",
            )
        )
        decision_engine = StubDecisionEngine(
            ModerationDecision(should_timeout=True, reason="Chatter toxicity threshold exceeded")
        )
        executor = StubExecutor()
        config = AppConfig(channel="channel", bot_username="bot", oauth_token="oauth:test", timeout_duration=42)
        service = ModerationService(
            rule_based_analyzer,
            MessageBuffer(10),
            executor,
            config,
            semantic_analyzer=semantic_analyzer,
            decision_engine=decision_engine,
        )

        service.handle_message(ChatMessage(username="user1", message="possible toxicity"))

        self.assertEqual(rule_based_analyzer.call_count, 1)
        self.assertEqual(semantic_analyzer.call_count, 1)
        self.assertEqual(decision_engine.call_count, 1)
        self.assertEqual(semantic_analyzer.last_request.streamer_identity, ["channel"])
        self.assertEqual(decision_engine.last_result.target, "chatter")
        self.assertEqual(len(executor.actions), 1)
        self.assertEqual(executor.actions[0].reason, "Chatter toxicity threshold exceeded")

    def test_service_ignores_semantic_result_when_decision_engine_rejects_timeout(self) -> None:
        rule_based_analyzer = StubRuleBasedAnalyzer(AnalysisResult(is_toxic=False, confidence=0.0, reason="No blacklist matches"))
        semantic_analyzer = StubSemanticAnalyzer(
            SemanticAnalysisResult(
                toxicity=0.3,
                target="game",
                confidence=0.9,
                reason="game insult",
            )
        )
        decision_engine = StubDecisionEngine(
            ModerationDecision(should_timeout=False, reason="Ignored target: game")
        )
        executor = StubExecutor()
        config = AppConfig(channel="channel", bot_username="bot", oauth_token="oauth:test", timeout_duration=42)
        service = ModerationService(
            rule_based_analyzer,
            MessageBuffer(10),
            executor,
            config,
            semantic_analyzer=semantic_analyzer,
            decision_engine=decision_engine,
        )

        service.handle_message(ChatMessage(username="user1", message="game insult"))

        self.assertEqual(semantic_analyzer.call_count, 1)
        self.assertEqual(decision_engine.call_count, 1)
        self.assertEqual(executor.actions, [])

    def test_service_logs_and_continues_when_semantic_analysis_fails(self) -> None:
        rule_based_analyzer = StubRuleBasedAnalyzer(AnalysisResult(is_toxic=False, confidence=0.0, reason="No blacklist matches"))
        semantic_analyzer = FailingSemanticAnalyzer(
            SemanticAnalyzerError("Semantic analyzer timed out after 5 seconds")
        )
        decision_engine = StubDecisionEngine(
            ModerationDecision(should_timeout=True, reason="Should not be used")
        )
        buffer = MessageBuffer(10)
        executor = StubExecutor()
        config = AppConfig(channel="channel", bot_username="bot", oauth_token="oauth:test", timeout_duration=42)
        service = ModerationService(
            rule_based_analyzer,
            buffer,
            executor,
            config,
            semantic_analyzer=semantic_analyzer,
            decision_engine=decision_engine,
        )

        with self.assertLogs("twitch_moderator.service", level="ERROR") as logs:
            service.handle_message(ChatMessage(username="user1", message="possible toxicity"))

        self.assertEqual(semantic_analyzer.call_count, 1)
        self.assertEqual(decision_engine.call_count, 0)
        self.assertEqual(executor.actions, [])
        self.assertEqual(buffer.snapshot(), [ChatMessage(username="user1", message="possible toxicity")])
        self.assertTrue(any("Semantic analysis failed" in entry for entry in logs.output))

    def test_service_logs_metrics_snapshot_on_interval(self) -> None:
        rule_based_analyzer = StubRuleBasedAnalyzer(AnalysisResult(is_toxic=False, confidence=0.0, reason="No blacklist matches"))
        semantic_analyzer = StubSemanticAnalyzer(
            SemanticAnalysisResult(
                toxicity=0.8,
                target="streamer",
                confidence=0.9,
                reason="semantic toxic",
            )
        )
        decision_engine = StubDecisionEngine(
            ModerationDecision(should_timeout=False, reason="Streamer toxicity below threshold")
        )
        executor = StubExecutor()
        metrics = RuntimeMetrics(log_every_messages=2)
        config = AppConfig(channel="channel", bot_username="bot", oauth_token="oauth:test", timeout_duration=42)
        service = ModerationService(
            rule_based_analyzer,
            MessageBuffer(10),
            executor,
            config,
            semantic_analyzer=semantic_analyzer,
            decision_engine=decision_engine,
            metrics=metrics,
        )

        with self.assertLogs("twitch_moderator.service", level="INFO") as logs:
            service.handle_message(ChatMessage(username="user1", message="first semantic"))
            service.handle_message(ChatMessage(username="user2", message="second semantic"))

        self.assertTrue(any("Metrics snapshot" in entry for entry in logs.output))


if __name__ == "__main__":
    unittest.main()
