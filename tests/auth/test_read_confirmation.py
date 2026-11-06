from datetime import UTC, datetime, timedelta
from typing import Any

from starlette.requests import Request

from bots_place.app.controllers.rest.routers.auth.depends.read_confirmation import (
    ReadConfirmation,
)
from bots_place.app.controllers.rest.routers.auth.utils.cookies import (
    CONFIRMATION_SESSION,
)
from bots_place.app.security.tokens import ConfirmationPurpose


def make_request(session: dict[str, Any]) -> Request:
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/auth/confirm",
        "headers": [],
        "query_string": b"",
        "session": session,
    }
    return Request(scope)


def make_session(
    *,
    expires_in: int = 900,
    email: str = "a@b.c",
    purpose: str = ConfirmationPurpose.REGISTER.value,
) -> dict[str, Any]:
    expires_at = datetime.now(UTC) + timedelta(seconds=expires_in)
    return {
        CONFIRMATION_SESSION: {
            "email": email,
            "purpose": purpose,
            "expires_at": expires_at.isoformat(),
        }
    }


async def test_empty_session_returns_none() -> None:
    result = await ReadConfirmation()(make_request({}))
    assert result is None


async def test_valid_session_returns_payload() -> None:
    result = await ReadConfirmation()(make_request(make_session()))
    assert result is not None
    assert result.email == "a@b.c"
    assert result.purpose is ConfirmationPurpose.REGISTER


async def test_expired_session_returns_none_and_is_removed() -> None:
    session = make_session(expires_in=-1)
    result = await ReadConfirmation()(make_request(session))
    assert result is None
    assert CONFIRMATION_SESSION not in session


async def test_malformed_session_returns_none_and_is_removed() -> None:
    session = {CONFIRMATION_SESSION: {"email": "a@b.c"}}
    result = await ReadConfirmation()(make_request(session))
    assert result is None
    assert CONFIRMATION_SESSION not in session


async def test_unknown_purpose_returns_none() -> None:
    result = await ReadConfirmation()(
        make_request(make_session(purpose="reset-password"))
    )
    assert result is None
