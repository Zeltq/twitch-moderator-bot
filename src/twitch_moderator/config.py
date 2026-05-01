from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


DEFAULT_BUFFER_SIZE = 10
DEFAULT_TIMEOUT_DURATION = 600
DEFAULT_IRC_HOST = "irc.chat.twitch.tv"
DEFAULT_IRC_PORT = 6697
DEFAULT_ANALYZER_TYPE = "rule_based"


@dataclass(frozen=True)
class AppConfig:
    channel: str
    bot_username: str
    oauth_token: str
    timeout_duration: int = DEFAULT_TIMEOUT_DURATION
    analyzer_type: str = DEFAULT_ANALYZER_TYPE
    buffer_size: int = DEFAULT_BUFFER_SIZE
    irc_host: str = DEFAULT_IRC_HOST
    irc_port: int = DEFAULT_IRC_PORT
    blacklist: tuple[str, ...] = ()

    @property
    def normalized_channel(self) -> str:
        return self.channel.lower().lstrip("#")


def load_dotenv(dotenv_path: str | Path = ".env") -> None:
    path = Path(dotenv_path)
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        if key and key not in os.environ:
            os.environ[key] = value


def load_config(dotenv_path: str | Path = ".env") -> AppConfig:
    load_dotenv(dotenv_path)

    channel = _require_env("TWITCH_CHANNEL")
    bot_username = _require_env("TWITCH_BOT_USERNAME")
    oauth_token = _normalize_token(_require_env("TWITCH_OAUTH_TOKEN"))

    timeout_duration = int(os.getenv("TWITCH_TIMEOUT_DURATION", DEFAULT_TIMEOUT_DURATION))
    buffer_size = int(os.getenv("MESSAGE_BUFFER_SIZE", DEFAULT_BUFFER_SIZE))
    analyzer_type = os.getenv("ANALYZER_TYPE", DEFAULT_ANALYZER_TYPE).strip()
    irc_host = os.getenv("TWITCH_IRC_HOST", DEFAULT_IRC_HOST).strip()
    irc_port = int(os.getenv("TWITCH_IRC_PORT", DEFAULT_IRC_PORT))
    blacklist = _parse_csv_env("BLACKLIST")

    return AppConfig(
        channel=channel,
        bot_username=bot_username,
        oauth_token=oauth_token,
        timeout_duration=timeout_duration,
        analyzer_type=analyzer_type,
        buffer_size=buffer_size,
        irc_host=irc_host,
        irc_port=irc_port,
        blacklist=blacklist,
    )


def _require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value


def _normalize_token(token: str) -> str:
    return token if token.startswith("oauth:") else f"oauth:{token}"


def _parse_csv_env(name: str) -> tuple[str, ...]:
    raw_value = os.getenv(name, "")
    parts = [part.strip() for part in raw_value.split(",")]
    return tuple(part for part in parts if part)

