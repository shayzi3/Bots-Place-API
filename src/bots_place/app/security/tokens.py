from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any

import jwt

from bots_place.config.env import JwtSettings
from bots_place.domain.exceptions.user import InvalidTokenError


class TokenType(StrEnum):
    ACCESS = "access"
    CONFIRMATION = "confirmation"


class ConfirmationPurpose(StrEnum):
    REGISTER = "register"
    LOGIN = "login"


@dataclass(frozen=True)
class AccessTokenPayload:
    user_id: int
    email: str


@dataclass(frozen=True)
class ConfirmationTokenPayload:
    email: str
    purpose: ConfirmationPurpose


class TokenService:
    def __init__(self, settings: JwtSettings) -> None:
        self._settings = settings

    @property
    def confirmation_ttl_seconds(self) -> int:
        return self._settings.pending_ttl_minutes * 60

    @property
    def access_ttl_seconds(self) -> int:
        return self._settings.access_ttl_minutes * 60

    def _encode(self, payload: dict[str, Any], ttl_seconds: int) -> str:
        now = datetime.now(UTC)
        payload["iat"] = now
        payload["exp"] = now + timedelta(seconds=ttl_seconds)
        return jwt.encode(
            payload,
            self._settings.secret,
            algorithm=self._settings.algorithm,
        )

    def _decode(self, token: str, expected_type: TokenType) -> dict[str, Any]:
        try:
            data: dict[str, Any] = jwt.decode(
                token,
                self._settings.secret,
                algorithms=[self._settings.algorithm],
            )
        except jwt.PyJWTError as exc:
            raise InvalidTokenError(str(exc)) from exc

        if data.get("type") != expected_type.value:
            raise InvalidTokenError(f"Expected a {expected_type.value} token")
        return data

    def create_access(self, user_id: int, email: str) -> str:
        return self._encode(
            {
                "type": TokenType.ACCESS.value,
                "sub": str(user_id),
                "email": email,
            },
            self.access_ttl_seconds,
        )

    def decode_access(self, token: str) -> AccessTokenPayload:
        data = self._decode(token, TokenType.ACCESS)
        try:
            return AccessTokenPayload(
                user_id=int(data["sub"]),
                email=data["email"],
            )
        except (KeyError, ValueError, TypeError) as exc:
            raise InvalidTokenError("Malformed access token") from exc

    def create_confirmation(self, email: str, purpose: ConfirmationPurpose) -> str:
        return self._encode(
            {
                "type": TokenType.CONFIRMATION.value,
                "email": email,
                "purpose": purpose.value,
            },
            self.confirmation_ttl_seconds,
        )

    def decode_confirmation(self, token: str) -> ConfirmationTokenPayload:
        data = self._decode(token, TokenType.CONFIRMATION)
        try:
            return ConfirmationTokenPayload(
                email=data["email"],
                purpose=ConfirmationPurpose(data["purpose"]),
            )
        except (KeyError, ValueError) as exc:
            raise InvalidTokenError("Malformed confirmation token") from exc
