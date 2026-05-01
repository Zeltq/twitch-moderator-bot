from __future__ import annotations

import logging

from twitch_moderator.analyzers.base import Analyzer
from twitch_moderator.buffer import MessageBuffer
from twitch_moderator.config import AppConfig
from twitch_moderator.executor import ActionExecutor
from twitch_moderator.models import ChatMessage, ModerationAction
from twitch_moderator.twitch_api import TwitchAPIError


LOGGER = logging.getLogger(__name__)


class ModerationService:
    def __init__(
        self,
        analyzer: Analyzer,
        message_buffer: MessageBuffer,
        executor: ActionExecutor,
        config: AppConfig,
    ) -> None:
        self._analyzer = analyzer
        self._message_buffer = message_buffer
        self._executor = executor
        self._config = config

    def handle_message(self, message: ChatMessage) -> None:
        context = self._message_buffer.snapshot()
        result = self._analyzer.analyze(message, context)

        LOGGER.info(
            "Analyzed message user=%s toxic=%s confidence=%.2f reason=%s",
            message.username,
            result.is_toxic,
            result.confidence,
            result.reason,
        )

        if result.is_toxic:
            action = ModerationAction(
                username=message.username,
                reason=result.reason,
                duration_seconds=self._config.timeout_duration,
            )
            try:
                self._executor.execute(action)
            except TwitchAPIError as exc:
                LOGGER.error(
                    "Moderation action rejected for user=%s reason=%s error=%s",
                    action.username,
                    action.reason,
                    exc,
                )
            except Exception:
                LOGGER.exception(
                    "Unexpected moderation failure for user=%s reason=%s",
                    action.username,
                    action.reason,
                )

        self._message_buffer.add(message)
