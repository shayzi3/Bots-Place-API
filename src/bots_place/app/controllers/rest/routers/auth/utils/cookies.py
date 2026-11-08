from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import Request, Response

from bots_place.app.security.tokens import (
    ConfirmationPurpose,
    ConfirmationTokenPayload,
)
from bots_place.config.env import CookieSettings

ACCESS_COOKIE = "access_token"
CONFIRMATION_SESSION = "confirmation_payload"


def set_auth_cookie(
    response: Response,
    name: str,
    value: str,
    max_age: int,
    settings: CookieSettings,
) -> None:
    response.set_cookie(
        key=name,
        value=value,
        max_age=max_age,
        httponly=True,
        secure=settings.secure,
        samesite=settings.samesite,
        domain=settings.domain,
        path="/",
    )


def clear_auth_cookie(
    response: Response,
    name: str,
    settings: CookieSettings,
) -> None:
    response.delete_cookie(
        key=name,
        domain=settings.domain,
        path="/",
    )


def set_request_session_confirmation(
    request: Request,
    email: str,
    purpose: ConfirmationPurpose,
    ttl_seconds: int,
    payload: dict[str, Any] | None = None,
) -> None:
    confirmation = ConfirmationTokenPayload(
        email=email,
        purpose=purpose,
        expires_at=datetime.now(UTC) + timedelta(seconds=ttl_seconds),
        payload=payload,
    )
    request.session[CONFIRMATION_SESSION] = confirmation.model_dump(mode="json")


def clear_request_session(request: Request) -> None:
    request.session.pop(CONFIRMATION_SESSION, None)
