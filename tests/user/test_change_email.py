import asyncio
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from bots_place.config.env import CodeSettings, JwtSettings
from bots_place.domain.commands import (
    ChangeUserEmailCommand,
    ConfirmEmailChangeCommand,
    UseEmailChangeLinkCommand,
)
from bots_place.domain.entities.email_change_request import (
    EmailChangeRequestBaseModel,
)
from bots_place.domain.entities.email_code import (
    EmailCodeBaseModel,
    EmailCodePurposeEnum,
)
from bots_place.domain.entities.user import UserAuthEnum, UserBaseModel
from bots_place.domain.exceptions import (
    EmailAlreadyExistsError,
    EmailChangeLinkInvalidError,
    InvalidEmailCodeError,
    ResendCooldownError,
)
from bots_place.infrastructure.commands import (
    ConfirmEmailChangeHandler,
    RequestEmailChangeHandler,
    UseEmailChangeLinkHandler,
)


@pytest.fixture
def uow() -> MagicMock:
    mock = MagicMock()
    mock.users = AsyncMock()
    mock.email_codes = AsyncMock()
    mock.email_change_requests = AsyncMock()
    mock.commit = AsyncMock()
    return mock


@pytest.fixture
def email_sender() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def jwt_settings() -> JwtSettings:
    return JwtSettings(
        secret="x" * 32,
        algorithm="HS256",
        access_ttl_minutes=60,
        pending_ttl_minutes=15,
    )


def make_user() -> UserBaseModel:
    return UserBaseModel(
        id=1,
        email="user@example.com",
        username="user",
        auth_from=UserAuthEnum.BASIC,
        is_verified=True,
        created_at=datetime.now(UTC),
    )


def make_request(
    *,
    created_at: datetime | None = None,
    used_at: datetime | None = None,
    expires_at: datetime | None = None,
) -> EmailChangeRequestBaseModel:
    now = datetime.now(UTC)
    return EmailChangeRequestBaseModel(
        id=uuid4(),
        user_id=1,
        new_email="new@example.com",
        expires_at=expires_at or now + timedelta(minutes=15),
        used_at=used_at,
        created_at=created_at or now,
    )


async def test_request_email_change_raises_on_cooldown(
    uow: MagicMock,
    email_sender: AsyncMock,
    jwt_settings: JwtSettings,
) -> None:
    uow.users.get.return_value = make_user()
    uow.users.email_exists.return_value = False
    uow.email_change_requests.get_latest_for_user.return_value = make_request(
        created_at=datetime.now(UTC) - timedelta(seconds=10)
    )
    handler = RequestEmailChangeHandler(uow, email_sender, jwt_settings)

    with pytest.raises(ResendCooldownError):
        await handler.handle(
            ChangeUserEmailCommand(
                user_id=1,
                new_email="new@example.com",
                link_url="http://test/api/v1/user/email",
            )
        )


async def test_request_email_change_sends_link_to_current_email(
    uow: MagicMock,
    email_sender: AsyncMock,
    jwt_settings: JwtSettings,
) -> None:
    user = make_user()
    uow.users.get.return_value = user
    uow.users.email_exists.return_value = False
    uow.email_change_requests.get_latest_for_user.return_value = None
    uow.email_change_requests.create.return_value = make_request()
    handler = RequestEmailChangeHandler(uow, email_sender, jwt_settings)

    await handler.handle(
        ChangeUserEmailCommand(
            user_id=1,
            new_email="new@example.com",
            link_url="http://test/api/v1/user/email",
        )
    )
    await asyncio.sleep(0)
    await asyncio.sleep(0)

    email_sender.send_link.assert_awaited_once()
    target, _ = email_sender.send_link.await_args.args
    assert target == user.email


async def test_request_email_change_raises_when_email_taken(
    uow: MagicMock,
    email_sender: AsyncMock,
    jwt_settings: JwtSettings,
) -> None:
    uow.users.get.return_value = make_user()
    uow.users.email_exists.return_value = True
    handler = RequestEmailChangeHandler(uow, email_sender, jwt_settings)

    with pytest.raises(EmailAlreadyExistsError):
        await handler.handle(
            ChangeUserEmailCommand(
                user_id=1,
                new_email="new@example.com",
                link_url="http://test/api/v1/user/email",
            )
        )


async def test_use_link_raises_for_invalid_token(
    uow: MagicMock,
    email_sender: AsyncMock,
    jwt_settings: JwtSettings,
) -> None:
    handler = UseEmailChangeLinkHandler(uow, email_sender, jwt_settings)

    with pytest.raises(EmailChangeLinkInvalidError):
        await handler.handle(UseEmailChangeLinkCommand(token="not-a-uuid"))


async def test_use_link_raises_for_used_link(
    uow: MagicMock,
    email_sender: AsyncMock,
    jwt_settings: JwtSettings,
) -> None:
    uow.email_change_requests.get.return_value = make_request(used_at=datetime.now(UTC))
    handler = UseEmailChangeLinkHandler(uow, email_sender, jwt_settings)

    with pytest.raises(EmailChangeLinkInvalidError):
        await handler.handle(UseEmailChangeLinkCommand(token=str(uuid4())))


async def test_confirm_email_change_raises_for_wrong_code(
    uow: MagicMock,
) -> None:
    uow.email_codes.get_active.return_value = EmailCodeBaseModel(
        id=1,
        email="new@example.com",
        code="123456",
        purpose=EmailCodePurposeEnum.CHANGE_EMAIL,
        expires_at=datetime.now(UTC) + timedelta(minutes=15),
        used_at=None,
        revoked=False,
        attempts=0,
        created_at=datetime.now(UTC),
    )
    handler = ConfirmEmailChangeHandler(uow, CodeSettings(resend_cooldown_seconds=60))

    with pytest.raises(InvalidEmailCodeError):
        await handler.handle(
            ConfirmEmailChangeCommand(user_id=1, email="new@example.com", code="000000")
        )
