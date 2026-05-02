import unittest

from twitch_moderator.metrics import RuntimeMetrics


class RuntimeMetricsTests(unittest.TestCase):
    def test_runtime_metrics_accumulates_counters(self) -> None:
        metrics = RuntimeMetrics(log_every_messages=10)

        metrics.record_message(toxicity=1.0, target=None, timed_out=True)
        metrics.record_message(toxicity=0.8, target="streamer", timed_out=True)
        metrics.record_message(toxicity=0.2, target="game", timed_out=False)

        snapshot = metrics.snapshot()

        self.assertEqual(snapshot.total_messages, 3)
        self.assertAlmostEqual(snapshot.average_toxicity, (1.0 + 0.8 + 0.2) / 3)
        self.assertEqual(snapshot.timeout_count, 2)
        self.assertEqual(snapshot.target_distribution, {"streamer": 1, "game": 1})

    def test_runtime_metrics_logs_on_configured_interval(self) -> None:
        metrics = RuntimeMetrics(log_every_messages=2)

        metrics.record_message(toxicity=0.0, target=None, timed_out=False)
        self.assertFalse(metrics.should_log_snapshot())

        metrics.record_message(toxicity=0.4, target="none", timed_out=False)
        self.assertTrue(metrics.should_log_snapshot())


if __name__ == "__main__":
    unittest.main()
