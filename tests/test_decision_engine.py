import unittest

from twitch_moderator.decision_engine import DecisionEngine, DecisionPolicy
from twitch_moderator.models import SemanticAnalysisResult


class DecisionEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = DecisionEngine(
            DecisionPolicy(
                streamer_threshold=0.5,
                chatter_threshold=0.6,
                none_threshold=0.85,
                min_confidence=0.4,
            )
        )

    def test_decision_engine_table_driven_targets(self) -> None:
        cases = [
            (
                "streamer above threshold",
                SemanticAnalysisResult(0.7, "streamer", 0.9, "x"),
                True,
                "Streamer toxicity threshold exceeded",
            ),
            (
                "streamer below threshold",
                SemanticAnalysisResult(0.4, "streamer", 0.9, "x"),
                False,
                "Streamer toxicity below threshold",
            ),
            (
                "chatter above threshold",
                SemanticAnalysisResult(0.7, "chatter", 0.9, "x"),
                True,
                "Chatter toxicity threshold exceeded",
            ),
            (
                "chatter below threshold",
                SemanticAnalysisResult(0.5, "chatter", 0.9, "x"),
                False,
                "Chatter toxicity below threshold",
            ),
            (
                "game ignored",
                SemanticAnalysisResult(1.0, "game", 0.9, "x"),
                False,
                "Ignored target: game",
            ),
            (
                "external ignored",
                SemanticAnalysisResult(1.0, "external", 0.9, "x"),
                False,
                "Ignored target: external",
            ),
        ]

        for name, result, should_timeout, reason in cases:
            with self.subTest(case=name):
                decision = self.engine.decide(result)
                self.assertEqual(decision.should_timeout, should_timeout)
                self.assertEqual(decision.reason, reason)

    def test_decision_engine_handles_none_target(self) -> None:
        timeout_decision = self.engine.decide(
            SemanticAnalysisResult(0.9, "none", 0.9, "x")
        )
        ignore_decision = self.engine.decide(
            SemanticAnalysisResult(0.6, "none", 0.9, "x")
        )

        self.assertTrue(timeout_decision.should_timeout)
        self.assertEqual(timeout_decision.reason, "Unspecified target toxicity threshold exceeded")
        self.assertFalse(ignore_decision.should_timeout)
        self.assertEqual(ignore_decision.reason, "Unspecified target toxicity below threshold")

    def test_decision_engine_rejects_low_confidence_before_target_logic(self) -> None:
        decision = self.engine.decide(
            SemanticAnalysisResult(1.0, "streamer", 0.2, "x")
        )

        self.assertFalse(decision.should_timeout)
        self.assertEqual(decision.reason, "Confidence below minimum threshold")


if __name__ == "__main__":
    unittest.main()
