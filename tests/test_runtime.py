import unittest

from twitch_moderator.config import AppConfig
from twitch_moderator.runtime import REQUIRED_MODERATION_SCOPE, build_runtime_context
from twitch_moderator.twitch_api import TokenInfo, UserInfo


class StubTwitchAPI:
    def __init__(self, token_info: TokenInfo) -> None:
        self._token_info = token_info
        self.lookups = []

    def validate_token(self) -> TokenInfo:
        return self._token_info

    def get_user_by_login(self, login: str) -> UserInfo:
        self.lookups.append(login)
        return UserInfo(user_id=f"id-{login}", login=login, display_name=login)


class RuntimeTests(unittest.TestCase):
    def test_runtime_context_requires_moderation_scope(self) -> None:
        config = AppConfig(channel="zeltq", bot_username="zeltq", oauth_token="oauth:test")
        twitch_api = StubTwitchAPI(
            TokenInfo(client_id="cid", login="zeltq", user_id="1", scopes=("chat:read", "chat:edit"))
        )

        with self.assertRaisesRegex(ValueError, REQUIRED_MODERATION_SCOPE):
            build_runtime_context(config, twitch_api)

    def test_runtime_context_builds_user_ids(self) -> None:
        config = AppConfig(channel="zeltq", bot_username="zeltq", oauth_token="oauth:test")
        twitch_api = StubTwitchAPI(
            TokenInfo(
                client_id="cid",
                login="zeltq",
                user_id="1",
                scopes=("chat:read", "chat:edit", REQUIRED_MODERATION_SCOPE),
            )
        )

        runtime = build_runtime_context(config, twitch_api)

        self.assertEqual(runtime.broadcaster.user_id, "id-zeltq")
        self.assertEqual(runtime.moderator.user_id, "id-zeltq")
        self.assertEqual(twitch_api.lookups, ["zeltq", "zeltq"])


if __name__ == "__main__":
    unittest.main()
