from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

from bots_place.app.security.sessions import hash_session_token, new_session_token
from bots_place.app.security.tokens import TokenService
from bots_place.config.env import JwtSettings
from bots_place.domain.commands import CreateSessionCommand, RevokeSessionCommand
from bots_place.infrastructure.commands import (
    CreateSessionHandler,
    RevokeSessionHandler,
)


def make_service(
    *, access_ttl_minutes: int = 60, pending_ttl_minutes: int = 15
) -> TokenService:
    return TokenService(
        JwtSettings(
            secret="x" * 32,
            algorithm="HS256",
            access_ttl_minutes=access_ttl_minutes,
            pending_ttl_minutes=pending_ttl_minutes,
        )
    )


def test_session_tokens_are_unique_and_hash_is_stable() -> None:
    first = new_session_token()
    second = new_session_token()

    assert first != second
    assert hash_session_token(first) == hash_session_token(first)
    assert hash_session_token(first) != first
    assert len(hash_session_token(first)) == 64


def test_ttl_properties_are_in_seconds() -> None:
    service = make_service(access_ttl_minutes=2, pending_ttl_minutes=1)

    assert service.access_ttl_seconds == 120
    assert service.confirmation_ttl_seconds == 60


async def test_create_session_stores_hash_not_raw_token() -> None:
    uow = MagicMock()
    uow.sessions = AsyncMock()
    handler = CreateSessionHandler(uow, make_service()._settings)

    token = await handler.handle(CreateSessionCommand(user_id=7))

    uow.sessions.create.assert_awaited_once()
    obj_in = uow.sessions.create.call_args.args[0]
    assert obj_in["user_id"] == 7
    assert obj_in["token_hash"] == hash_session_token(token)
    assert obj_in["token_hash"] != token
    assert obj_in["expires_at"] > datetime.now(UTC) + timedelta(minutes=59)


async def test_revoke_session_marks_row_by_token_hash() -> None:
    uow = MagicMock()
    uow.sessions = AsyncMock()
    handler = RevokeSessionHandler(uow)

    await handler.handle(RevokeSessionCommand(token="raw-token"))

    uow.sessions.update.assert_awaited_once()
    obj_in = uow.sessions.update.call_args.kwargs["obj_in"]
    assert set(obj_in) == {"revoked_at"}
