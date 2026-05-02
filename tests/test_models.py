import unittest

from twitch_moderator.models import ModerationDecision, SemanticAnalysisResult


class SemanticAnalysisResultTests(unittest.TestCase):
    def test_semantic_analysis_result_round_trip(self) -> None:
        result = SemanticAnalysisResult(
            toxicity=0.85,
            target="streamer",
            confidence=0.9,
            reason="Direct insult toward streamer",
        )

        self.assertEqual(
            result.to_dict(),
            {
                "toxicity": 0.85,
                "target": "streamer",
                "confidence": 0.9,
                "reason": "Direct insult toward streamer",
            },
        )
        self.assertEqual(SemanticAnalysisResult.from_dict(result.to_dict()), result)

    def test_semantic_analysis_result_rejects_invalid_target(self) -> None:
        with self.assertRaisesRegex(ValueError, "target must be one of"):
            SemanticAnalysisResult(
                toxicity=0.5,
                target="viewer",  # type: ignore[arg-type]
                confidence=0.5,
                reason="bad target",
            )

    def test_semantic_analysis_result_rejects_out_of_range_scores(self) -> None:
        with self.assertRaisesRegex(ValueError, "toxicity must be between 0.0 and 1.0"):
            SemanticAnalysisResult(
                toxicity=1.5,
                target="none",
                confidence=0.5,
                reason="bad toxicity",
            )

    def test_semantic_analysis_result_requires_expected_payload_fields(self) -> None:
        with self.assertRaisesRegex(ValueError, "Missing required field: reason"):
            SemanticAnalysisResult.from_dict(
                {
                    "toxicity": 0.2,
                    "target": "game",
                    "confidence": 0.7,
                }
            )


class ModerationDecisionTests(unittest.TestCase):
    def test_moderation_decision_serializes(self) -> None:
        decision = ModerationDecision(should_timeout=True, reason="Streamer threshold exceeded")

        self.assertEqual(
            decision.to_dict(),
            {
                "should_timeout": True,
                "reason": "Streamer threshold exceeded",
            },
        )


if __name__ == "__main__":
    unittest.main()
