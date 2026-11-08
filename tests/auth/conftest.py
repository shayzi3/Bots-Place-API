from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from bots_place.app.security.sessions import hash_session_token, new_session_token
from bots_place.config.env import CodeSettings, JwtSettings
from bots_place.domain.entities.email_code import (
    EmailCodeBaseModel,
    EmailCodePurposeEnum,
)
from bots_place.domain.entities.user import UserAuthEnum, UserBaseModel
from bots_place.domain.entities.user_session import UserSessionBaseModel


@pytest.fixture
def uow() -> MagicMock:
    mock = MagicMock()
    mock.users = AsyncMock()
    mock.email_codes = AsyncMock()
    mock.sessions = AsyncMock()
    mock.commit = AsyncMock()
    mock.rollback = AsyncMock()
    return mock


@pytest.fixture
def email_sender() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def code_settings() -> CodeSettings:
    return CodeSettings(resend_cooldown_seconds=60)


@pytest.fixture
def jwt_settings() -> JwtSettings:
    return JwtSettings(
        secret="x" * 32,
        algorithm="HS256",
        access_ttl_minutes=60,
        pending_ttl_minutes=15,
    )


@pytest.fixture
def make_user() -> Callable[..., UserBaseModel]:
    def _make(
        *,
        id: int = 1,
        email: str = "user@example.com",
        is_verified: bool = True,
    ) -> UserBaseModel:
        return UserBaseModel(
            id=id,
            email=email,
            username="user",
            auth_from=UserAuthEnum.BASIC,
            is_verified=is_verified,
            created_at=datetime.now(UTC),
        )

    return _make


@pytest.fixture
def make_code() -> Callable[..., EmailCodeBaseModel]:
    def _make(
        *,
        id: int = 1,
        email: str = "user@example.com",
        code: str = "123456",
        purpose: EmailCodePurposeEnum = EmailCodePurposeEnum.REGISTRATION,
        created_at: datetime | None = None,
        attempts: int = 0,
    ) -> EmailCodeBaseModel:
        now = datetime.now(UTC)
        return EmailCodeBaseModel(
            id=id,
            email=email,
            code=code,
            purpose=purpose,
            expires_at=now + timedelta(minutes=15),
            used_at=None,
            revoked=False,
            attempts=attempts,
            created_at=created_at or now,
        )

    return _make


@pytest.fixture
def make_session(uow: MagicMock) -> Callable[[int], str]:
    def _make(user_id: int) -> str:
        token = new_session_token()
        uow.sessions.get.return_value = UserSessionBaseModel(
            id=1,
            user_id=user_id,
            token_hash=hash_session_token(token),
            expires_at=datetime.now(UTC) + timedelta(minutes=5),
            revoked_at=None,
            created_at=datetime.now(UTC),
        )
        return token

    return _make
