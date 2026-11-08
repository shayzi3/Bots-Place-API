from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel

from bots_place.config.env import JwtSettings


class ConfirmationPurpose(StrEnum):
    REGISTER = "register"
    LOGIN = "login"
    CHANGE_EMAIL = "change_email"


class ConfirmationTokenPayload(BaseModel):
    email: str
    purpose: ConfirmationPurpose
    expires_at: datetime
    payload: dict[str, Any] | None = None


class TokenService:
    def __init__(self, settings: JwtSettings) -> None:
        self._settings = settings

    @property
    def confirmation_ttl_seconds(self) -> int:
        return self._settings.pending_ttl_minutes * 60

    @property
    def access_ttl_seconds(self) -> int:
        return self._settings.access_ttl_minutes * 60
