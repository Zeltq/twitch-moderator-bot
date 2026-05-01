from __future__ import annotations

import logging
import socket
import ssl
import time
from dataclasses import dataclass

from twitch_moderator.models import ChatMessage


LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class IRCConfig:
    host: str
    port: int
    nickname: str
    oauth_token: str
    channel: str


class TwitchIRCClient:
    def __init__(self, config: IRCConfig, reconnect_delay_seconds: int = 5) -> None:
        self._config = config
        self._reconnect_delay_seconds = reconnect_delay_seconds
        self._socket: ssl.SSLSocket | None = None
        self._reader = None
        self._writer = None

    def connect(self) -> None:
        LOGGER.info("Connecting to Twitch IRC %s:%s", self._config.host, self._config.port)
        raw_socket = socket.create_connection((self._config.host, self._config.port))
        tls_socket = ssl.create_default_context().wrap_socket(raw_socket, server_hostname=self._config.host)

        self._socket = tls_socket
        self._reader = tls_socket.makefile("r", encoding="utf-8", newline="\r\n")
        self._writer = tls_socket.makefile("w", encoding="utf-8", newline="\r\n")

        self._send_line(f"PASS {self._config.oauth_token}")
        self._send_line(f"NICK {self._config.nickname}")
        self._send_line(f"JOIN #{self._config.channel}")
        self._complete_handshake()
        LOGGER.info("Joined channel #%s", self._config.channel)

    def run_forever(self, on_message) -> None:
        while True:
            try:
                self.connect()
                self._read_loop(on_message)
            except OSError:
                LOGGER.exception("IRC connection failed; reconnecting in %s seconds", self._reconnect_delay_seconds)
                self.close()
                time.sleep(self._reconnect_delay_seconds)

    def send_privmsg(self, message: str) -> None:
        self._send_line(f"PRIVMSG #{self._config.channel} :{message}")

    def close(self) -> None:
        if self._reader is not None:
            self._reader.close()
        if self._writer is not None:
            self._writer.close()
        if self._socket is not None:
            self._socket.close()

        self._socket = None
        self._reader = None
        self._writer = None

    def _read_loop(self, on_message) -> None:
        if self._reader is None:
            raise RuntimeError("IRC client is not connected")

        for line in self._reader:
            payload = line.rstrip("\r\n")
            if not payload:
                continue

            LOGGER.debug("IRC << %s", payload)
            if payload.startswith("PING "):
                self._send_line(payload.replace("PING", "PONG", 1))
                continue

            if " NOTICE " in payload:
                LOGGER.info("IRC notice: %s", payload)
                if "Login authentication failed" in payload:
                    raise OSError("IRC authentication failed")
                continue

            message = parse_privmsg(payload)
            if message is not None:
                on_message(message)

        raise OSError("IRC connection closed")

    def _send_line(self, line: str) -> None:
        if self._writer is None:
            raise RuntimeError("IRC client is not connected")

        LOGGER.debug("IRC >> %s", line)
        self._writer.write(f"{line}\r\n")
        self._writer.flush()

    def _complete_handshake(self) -> None:
        if self._reader is None:
            raise RuntimeError("IRC client is not connected")

        saw_join_confirmation = False
        saw_auth_confirmation = False

        for line in self._reader:
            payload = line.rstrip("\r\n")
            if not payload:
                continue

            LOGGER.debug("IRC << %s", payload)

            if payload.startswith("PING "):
                self._send_line(payload.replace("PING", "PONG", 1))
                continue

            if " NOTICE " in payload:
                LOGGER.info("IRC notice: %s", payload)
                if "Login authentication failed" in payload:
                    raise OSError("IRC authentication failed")
                if "Improperly formatted auth" in payload:
                    raise OSError("IRC authentication token format is invalid")

            if " 001 " in payload:
                saw_auth_confirmation = True

            if f" JOIN #{self._config.channel}" in payload or f" ROOMSTATE #{self._config.channel}" in payload:
                saw_join_confirmation = True

            if saw_auth_confirmation and saw_join_confirmation:
                return

        raise OSError("IRC connection closed during handshake")


def parse_privmsg(raw_line: str) -> ChatMessage | None:
    if " PRIVMSG " not in raw_line or not raw_line.startswith(":"):
        return None

    prefix, trailing = raw_line.split(" :", 1)
    username = prefix[1:].split("!", 1)[0]
    return ChatMessage(username=username, message=trailing)
