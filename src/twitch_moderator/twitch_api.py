from __future__ import annotations

import json
import logging
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass


LOGGER = logging.getLogger(__name__)

VALIDATE_URL = "https://id.twitch.tv/oauth2/validate"
HELIX_USERS_URL = "https://api.twitch.tv/helix/users"
HELIX_BANS_URL = "https://api.twitch.tv/helix/moderation/bans"


@dataclass(frozen=True)
class TokenInfo:
    client_id: str
    login: str
    user_id: str
    scopes: tuple[str, ...]


@dataclass(frozen=True)
class UserInfo:
    user_id: str
    login: str
    display_name: str


class TwitchAPIError(RuntimeError):
    pass


class TwitchAPIClient:
    def __init__(self, oauth_token: str, timeout_seconds: int = 10) -> None:
        self._oauth_token = oauth_token
        self._timeout_seconds = timeout_seconds
        self._cached_token_info: TokenInfo | None = None

    def validate_token(self) -> TokenInfo:
        payload = self._request_json(
            VALIDATE_URL,
            headers={"Authorization": f"OAuth {self._bearer_token}"},
        )

        token_info = TokenInfo(
            client_id=payload["client_id"],
            login=payload["login"],
            user_id=str(payload["user_id"]),
            scopes=tuple(payload.get("scopes", [])),
        )
        self._cached_token_info = token_info
        return token_info

    def get_user_by_login(self, login: str) -> UserInfo:
        token_info = self._get_or_validate_token_info()
        query = urllib.parse.urlencode({"login": login})
        payload = self._request_json(
            f"{HELIX_USERS_URL}?{query}",
            headers=self._helix_headers(token_info.client_id),
        )

        users = payload.get("data", [])
        if not users:
            raise TwitchAPIError(f"Twitch user not found for login: {login}")

        user = users[0]
        return UserInfo(
            user_id=str(user["id"]),
            login=user["login"],
            display_name=user["display_name"],
        )

    def timeout_user(
        self,
        broadcaster_id: str,
        moderator_id: str,
        target_user_id: str,
        duration_seconds: int,
        reason: str,
    ) -> None:
        token_info = self._get_or_validate_token_info()
        query = urllib.parse.urlencode(
            {
                "broadcaster_id": broadcaster_id,
                "moderator_id": moderator_id,
            }
        )
        body = {
            "data": {
                "user_id": target_user_id,
                "duration": duration_seconds,
                "reason": reason[:500],
            }
        }

        self._request_json(
            f"{HELIX_BANS_URL}?{query}",
            headers=self._helix_headers(token_info.client_id),
            body=body,
            method="POST",
        )
        LOGGER.info(
            "Timeout request sent via Helix broadcaster_id=%s moderator_id=%s target_user_id=%s duration=%s",
            broadcaster_id,
            moderator_id,
            target_user_id,
            duration_seconds,
        )

    @property
    def _bearer_token(self) -> str:
        return self._oauth_token.removeprefix("oauth:")

    def _get_or_validate_token_info(self) -> TokenInfo:
        if self._cached_token_info is None:
            return self.validate_token()
        return self._cached_token_info

    def _helix_headers(self, client_id: str) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._bearer_token}",
            "Client-Id": client_id,
            "Content-Type": "application/json",
        }

    def _request_json(
        self,
        url: str,
        headers: dict[str, str],
        body: dict | None = None,
        method: str = "GET",
    ) -> dict:
        data = None
        if body is not None:
            data = json.dumps(body).encode("utf-8")

        request = urllib.request.Request(url=url, data=data, method=method)
        for name, value in headers.items():
            request.add_header(name, value)

        try:
            with urllib.request.urlopen(request, timeout=self._timeout_seconds) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            raw_body = exc.read().decode("utf-8", errors="replace")
            raise TwitchAPIError(f"Twitch API request failed {exc.code}: {raw_body}") from exc
        except urllib.error.URLError as exc:
            raise TwitchAPIError(f"Twitch API request failed: {exc.reason}") from exc
