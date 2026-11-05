import asyncio
from datetime import UTC, datetime, timedelta

import pytest

from bots_place.domain.commands import ResendCodeCommand
from bots_place.domain.entities.email_code import EmailCodePurposeEnum
from bots_place.domain.exceptions.user import (
    ResendCooldownError,
    ResendNotAllowedError,
)
from bots_place.infrastructure.commands.resend import ResendCodeHandler


async def test_resend_registration_code_refuses_old_and_sends_new(
    uow, email_sender, code_settings, jwt_settings, make_user, make_code
) -> None:
    uow.users.get_by_email.return_value = make_user(is_verified=False)
    uow.email_codes.get_active.return_value = make_code(
        id=5,
        created_at=datetime.now(UTC) - timedelta(seconds=120),
    )

    handler = ResendCodeHandler(uow, email_sender, code_settings, jwt_settings)
    await handler.handle(
        ResendCodeCommand(
            email="user@example.com", purpose=EmailCodePurposeEnum.REGISTRATION
        )
    )
    await asyncio.sleep(0)

    uow.email_codes.update.assert_awaited_once()
    assert uow.email_codes.update.call_args.kwargs["obj_in"] == {"revoked": True}
    uow.email_codes.create.assert_awaited_once()
    payload = uow.email_codes.create.call_args.args[0]
    assert payload["purpose"] == "registration"
    assert payload["email"] == "user@example.com"
    uow.commit.assert_awaited_once()
    email_sender.send_code.assert_awaited_once_with("user@example.com", payload["code"])


async def test_resend_login_code_for_verified_user(
    uow, email_sender, code_settings, jwt_settings, make_user
) -> None:
    uow.users.get_by_email.return_value = make_user(is_verified=True)
    uow.email_codes.get_active.return_value = None

    handler = ResendCodeHandler(uow, email_sender, code_settings, jwt_settings)
    await handler.handle(
        ResendCodeCommand(email="user@example.com", purpose=EmailCodePurposeEnum.LOGIN)
    )
    await asyncio.sleep(0)

    uow.email_codes.update.assert_not_awaited()
    assert uow.email_codes.create.call_args.args[0]["purpose"] == "login"
    email_sender.send_code.assert_awaited_once()


async def test_resend_during_cooldown_raises_with_remaining_seconds(
    uow, email_sender, code_settings, jwt_settings, make_user, make_code
) -> None:
    uow.users.get_by_email.return_value = make_user(is_verified=False)
    uow.email_codes.get_active.return_value = make_code(
        created_at=datetime.now(UTC) - timedelta(seconds=20),
    )

    handler = ResendCodeHandler(uow, email_sender, code_settings, jwt_settings)
    with pytest.raises(ResendCooldownError) as exc_info:
        await handler.handle(
            ResendCodeCommand(
                email="user@example.com", purpose=EmailCodePurposeEnum.REGISTRATION
            )
        )

    assert 39 <= exc_info.value.retry_after <= 40
    uow.email_codes.update.assert_not_awaited()
    uow.email_codes.create.assert_not_awaited()
    email_sender.send_code.assert_not_awaited()


async def test_resend_unknown_user_is_not_allowed(
    uow, email_sender, code_settings, jwt_settings
) -> None:
    uow.users.get_by_email.return_value = None

    handler = ResendCodeHandler(uow, email_sender, code_settings, jwt_settings)
    with pytest.raises(ResendNotAllowedError):
        await handler.handle(
            ResendCodeCommand(
                email="ghost@example.com", purpose=EmailCodePurposeEnum.REGISTRATION
            )
        )

    uow.email_codes.create.assert_not_awaited()


async def test_resend_registration_for_verified_user_is_not_allowed(
    uow, email_sender, code_settings, jwt_settings, make_user
) -> None:
    uow.users.get_by_email.return_value = make_user(is_verified=True)

    handler = ResendCodeHandler(uow, email_sender, code_settings, jwt_settings)
    with pytest.raises(ResendNotAllowedError):
        await handler.handle(
            ResendCodeCommand(
                email="user@example.com", purpose=EmailCodePurposeEnum.REGISTRATION
            )
        )

    uow.email_codes.create.assert_not_awaited()


async def test_resend_login_for_unverified_user_is_not_allowed(
    uow, email_sender, code_settings, jwt_settings, make_user
) -> None:
    uow.users.get_by_email.return_value = make_user(is_verified=False)

    handler = ResendCodeHandler(uow, email_sender, code_settings, jwt_settings)
    with pytest.raises(ResendNotAllowedError):
        await handler.handle(
            ResendCodeCommand(
                email="user@example.com", purpose=EmailCodePurposeEnum.LOGIN
            )
        )

    uow.email_codes.create.assert_not_awaited()
