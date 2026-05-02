import os
import unittest
from pathlib import Path

from twitch_moderator.config import AppConfig, load_config


class ConfigTests(unittest.TestCase):
    def test_load_config_reads_dotenv(self) -> None:
        dotenv_path = Path("tests/.tmp.env")
        dotenv_path.write_text(
            "\n".join(
                [
                    "TWITCH_CHANNEL=test_channel",
                    "TWITCH_BOT_USERNAME=test_bot",
                    "TWITCH_OAUTH_TOKEN=test_token",
                    "BLACKLIST=spam, insult ",
                    "STREAMER_THRESHOLD=0.55",
                    "CHATTER_THRESHOLD=0.65",
                    "NONE_THRESHOLD=0.9",
                    "MIN_CONFIDENCE=0.4",
                    "LLM_TIMEOUT_SECONDS=7",
                    "LLM_RETRY_COUNT=3",
                ]
            ),
            encoding="utf-8",
        )

        original_values = {key: os.environ.get(key) for key in _MANAGED_ENV_KEYS}
        try:
            for key in _MANAGED_ENV_KEYS:
                os.environ.pop(key, None)

            config = load_config(dotenv_path)

            self.assertEqual(config.channel, "test_channel")
            self.assertEqual(config.bot_username, "test_bot")
            self.assertEqual(config.oauth_token, "oauth:test_token")
            self.assertEqual(config.blacklist, ("spam", "insult"))
            self.assertEqual(config.streamer_threshold, 0.55)
            self.assertEqual(config.chatter_threshold, 0.65)
            self.assertEqual(config.none_threshold, 0.9)
            self.assertEqual(config.min_confidence, 0.4)
            self.assertEqual(config.llm_timeout_seconds, 7)
            self.assertEqual(config.llm_retry_count, 3)
        finally:
            for key, value in original_values.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

            if dotenv_path.exists():
                dotenv_path.unlink()

    def test_app_config_rejects_invalid_threshold(self) -> None:
        with self.assertRaisesRegex(ValueError, "streamer_threshold must be between 0.0 and 1.0"):
            AppConfig(
                channel="channel",
                bot_username="bot",
                oauth_token="oauth:test",
                streamer_threshold=1.5,
            )


_MANAGED_ENV_KEYS = [
    "TWITCH_CHANNEL",
    "TWITCH_BOT_USERNAME",
    "TWITCH_OAUTH_TOKEN",
    "BLACKLIST",
    "STREAMER_THRESHOLD",
    "CHATTER_THRESHOLD",
    "NONE_THRESHOLD",
    "MIN_CONFIDENCE",
    "LLM_TIMEOUT_SECONDS",
    "LLM_RETRY_COUNT",
]


if __name__ == "__main__":
    unittest.main()
