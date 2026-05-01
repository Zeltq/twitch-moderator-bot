import unittest

from twitch_moderator.buffer import MessageBuffer
from twitch_moderator.config import AppConfig
from twitch_moderator.models import AnalysisResult, ChatMessage
from twitch_moderator.service import ModerationService
from twitch_moderator.twitch_api import TwitchAPIError


class StubAnalyzer:
    def __init__(self, result: AnalysisResult) -> None:
        self._result = result
        self.last_context = None

    def analyze(self, current_message: ChatMessage, context: list[ChatMessage]) -> AnalysisResult:
        self.last_context = context
        return self._result


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
        analyzer = StubAnalyzer(AnalysisResult(is_toxic=False, confidence=0.0, reason="ok"))
        executor = StubExecutor()
        config = AppConfig(channel="channel", bot_username="bot", oauth_token="oauth:test")
        service = ModerationService(analyzer, MessageBuffer(10), executor, config)

        service.handle_message(ChatMessage(username="user1", message="first"))
        service.handle_message(ChatMessage(username="user2", message="second"))

        self.assertEqual(analyzer.last_context, [ChatMessage(username="user1", message="first")])
        self.assertEqual(executor.actions, [])

    def test_service_executes_timeout_for_toxic_messages(self) -> None:
        analyzer = StubAnalyzer(AnalysisResult(is_toxic=True, confidence=1.0, reason="Matched blacklist: spam"))
        executor = StubExecutor()
        config = AppConfig(channel="channel", bot_username="bot", oauth_token="oauth:test", timeout_duration=42)
        service = ModerationService(analyzer, MessageBuffer(10), executor, config)

        service.handle_message(ChatMessage(username="user1", message="spam"))

        self.assertEqual(len(executor.actions), 1)
        self.assertEqual(executor.actions[0].username, "user1")
        self.assertEqual(executor.actions[0].duration_seconds, 42)

    def test_service_logs_and_continues_when_timeout_fails(self) -> None:
        analyzer = StubAnalyzer(AnalysisResult(is_toxic=True, confidence=1.0, reason="Matched blacklist: spam"))
        executor = FailingExecutor()
        buffer = MessageBuffer(10)
        config = AppConfig(channel="channel", bot_username="bot", oauth_token="oauth:test", timeout_duration=42)
        service = ModerationService(analyzer, buffer, executor, config)

        with self.assertLogs("twitch_moderator.service", level="WARNING") as logs:
            service.handle_message(ChatMessage(username="user1", message="spam"))

        self.assertEqual(len(executor.actions), 1)
        self.assertEqual(buffer.snapshot(), [ChatMessage(username="user1", message="spam")])
        self.assertTrue(any("Moderation action rejected" in entry for entry in logs.output))


if __name__ == "__main__":
    unittest.main()
