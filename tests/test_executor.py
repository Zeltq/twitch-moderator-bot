import unittest

from twitch_moderator.executor import ActionExecutor
from twitch_moderator.models import ModerationAction
from twitch_moderator.twitch_api import UserInfo


class StubTwitchAPI:
    def __init__(self) -> None:
        self.lookups = []
        self.timeout_calls = []

    def get_user_by_login(self, login: str) -> UserInfo:
        self.lookups.append(login)
        return UserInfo(user_id="123", login=login, display_name=login)

    def timeout_user(
        self,
        broadcaster_id: str,
        moderator_id: str,
        target_user_id: str,
        duration_seconds: int,
        reason: str,
    ) -> None:
        self.timeout_calls.append(
            {
                "broadcaster_id": broadcaster_id,
                "moderator_id": moderator_id,
                "target_user_id": target_user_id,
                "duration_seconds": duration_seconds,
                "reason": reason,
            }
        )


class ActionExecutorTests(unittest.TestCase):
    def test_executor_uses_helix_timeout(self) -> None:
        twitch_api = StubTwitchAPI()
        executor = ActionExecutor(
            twitch_api=twitch_api,
            broadcaster_id="10",
            moderator_id="20",
        )

        executor.execute(ModerationAction(username="target_user", reason="Matched blacklist: spam", duration_seconds=600))

        self.assertEqual(twitch_api.lookups, ["target_user"])
        self.assertEqual(
            twitch_api.timeout_calls,
            [
                {
                    "broadcaster_id": "10",
                    "moderator_id": "20",
                    "target_user_id": "123",
                    "duration_seconds": 600,
                    "reason": "Matched blacklist: spam",
                }
            ],
        )


if __name__ == "__main__":
    unittest.main()

