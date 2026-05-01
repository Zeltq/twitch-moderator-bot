from __future__ import annotations

from dataclasses import dataclass

from twitch_moderator.config import AppConfig
from twitch_moderator.twitch_api import TokenInfo, TwitchAPIClient, UserInfo


REQUIRED_MODERATION_SCOPE = "moderator:manage:banned_users"


@dataclass(frozen=True)
class RuntimeContext:
    token_info: TokenInfo
    broadcaster: UserInfo
    moderator: UserInfo


def build_runtime_context(config: AppConfig, twitch_api: TwitchAPIClient) -> RuntimeContext:
    token_info = twitch_api.validate_token()
    if token_info.login != config.bot_username.lower():
        raise ValueError(
            "TWITCH_BOT_USERNAME must match the Twitch login associated with TWITCH_OAUTH_TOKEN"
        )

    if REQUIRED_MODERATION_SCOPE not in token_info.scopes:
        raise ValueError(
            "TWITCH_OAUTH_TOKEN is missing required scope moderator:manage:banned_users"
        )

    broadcaster = twitch_api.get_user_by_login(config.normalized_channel)
    moderator = twitch_api.get_user_by_login(config.bot_username.lower())
    return RuntimeContext(
        token_info=token_info,
        broadcaster=broadcaster,
        moderator=moderator,
    )

