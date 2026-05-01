from __future__ import annotations

import logging

from twitch_moderator.models import ModerationAction
from twitch_moderator.twitch_api import TwitchAPIClient


LOGGER = logging.getLogger(__name__)


class ActionExecutor:
    def __init__(
        self,
        twitch_api: TwitchAPIClient,
        broadcaster_id: str,
        moderator_id: str,
    ) -> None:
        self._twitch_api = twitch_api
        self._broadcaster_id = broadcaster_id
        self._moderator_id = moderator_id

    def execute(self, action: ModerationAction) -> None:
        LOGGER.info("Issuing timeout for user=%s duration=%s", action.username, action.duration_seconds)
        target_user = self._twitch_api.get_user_by_login(action.username)
        self._twitch_api.timeout_user(
            broadcaster_id=self._broadcaster_id,
            moderator_id=self._moderator_id,
            target_user_id=target_user.user_id,
            duration_seconds=action.duration_seconds,
            reason=action.reason,
        )
