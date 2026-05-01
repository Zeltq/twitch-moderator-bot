from __future__ import annotations

from collections import deque

from twitch_moderator.models import ChatMessage


class MessageBuffer:
    def __init__(self, max_size: int) -> None:
        if max_size <= 0:
            raise ValueError("max_size must be greater than zero")
        self._messages: deque[ChatMessage] = deque(maxlen=max_size)

    def add(self, message: ChatMessage) -> None:
        self._messages.append(message)

    def snapshot(self) -> list[ChatMessage]:
        return list(self._messages)

