import unittest

from twitch_moderator.irc import parse_privmsg
from twitch_moderator.models import ChatMessage


class IRCTests(unittest.TestCase):
    def test_parse_privmsg_returns_chat_message(self) -> None:
        raw_line = ":some_user!some_user@some_user.tmi.twitch.tv PRIVMSG #channel :hello world"

        self.assertEqual(
            parse_privmsg(raw_line),
            ChatMessage(username="some_user", message="hello world"),
        )

    def test_parse_privmsg_ignores_non_chat_lines(self) -> None:
        self.assertIsNone(parse_privmsg("PING :tmi.twitch.tv"))


if __name__ == "__main__":
    unittest.main()
