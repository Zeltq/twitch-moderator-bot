import unittest

from twitch_moderator.buffer import MessageBuffer
from twitch_moderator.models import ChatMessage


class MessageBufferTests(unittest.TestCase):
    def test_message_buffer_keeps_latest_messages(self) -> None:
        buffer = MessageBuffer(max_size=2)

        buffer.add(ChatMessage(username="user1", message="first"))
        buffer.add(ChatMessage(username="user2", message="second"))
        buffer.add(ChatMessage(username="user3", message="third"))

        self.assertEqual(
            buffer.snapshot(),
            [
                ChatMessage(username="user2", message="second"),
                ChatMessage(username="user3", message="third"),
            ],
        )


if __name__ == "__main__":
    unittest.main()
