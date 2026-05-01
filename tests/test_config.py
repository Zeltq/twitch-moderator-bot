import os
import unittest
from pathlib import Path

from twitch_moderator.config import load_config


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
        finally:
            for key, value in original_values.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

            if dotenv_path.exists():
                dotenv_path.unlink()


_MANAGED_ENV_KEYS = [
    "TWITCH_CHANNEL",
    "TWITCH_BOT_USERNAME",
    "TWITCH_OAUTH_TOKEN",
    "BLACKLIST",
]


if __name__ == "__main__":
    unittest.main()
