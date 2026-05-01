import unittest

from twitch_moderator.analyzers.rule_based import RuleBasedAnalyzer
from twitch_moderator.models import ChatMessage


class RuleBasedAnalyzerTests(unittest.TestCase):
    def test_rule_based_analyzer_detects_blacklist_case_insensitively(self) -> None:
        analyzer = RuleBasedAnalyzer(["дебил"])

        result = analyzer.analyze(
            ChatMessage(username="user1", message="Какой же ты ДЕБИЛ"),
            context=[],
        )

        self.assertTrue(result.is_toxic)
        self.assertEqual(result.confidence, 1.0)
        self.assertIn("дебил", result.reason)

    def test_rule_based_analyzer_returns_non_toxic_when_no_match(self) -> None:
        analyzer = RuleBasedAnalyzer(["дебил"])

        result = analyzer.analyze(
            ChatMessage(username="user1", message="всем привет"),
            context=[],
        )

        self.assertFalse(result.is_toxic)
        self.assertEqual(result.confidence, 0.0)


if __name__ == "__main__":
    unittest.main()
