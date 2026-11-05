import asyncio
from datetime import UTC, datetime, timedelta

import pytest

from bots_place.domain.commands import ConfirmLoginCommand, RequestLoginCodeCommand
from bots_place.domain.entities.email_code import EmailCodePurposeEnum
from bots_place.domain.exceptions.user import (
    InvalidEmailCodeError,
    LoginNotAllowedError,
)
from bots_place.infrastructure.commands.login import (
    ConfirmLoginHandler,
    RequestLoginCodeHandler,
)


async def test_request_login_code_unknown_email(
    uow, email_sender, jwt_settings
) -> None:
    uow.users.get_by_email.return_value = None

    handler = RequestLoginCodeHandler(uow, email_sender, jwt_settings)
    with pytest.raises(LoginNotAllowedError):
        await handler.handle(RequestLoginCodeCommand(email="ghost@example.com"))

    uow.email_codes.create.assert_not_awaited()
    email_sender.send_code.assert_not_awaited()


async def test_request_login_code_sets_expiry_from_pending_ttl(
    uow, email_sender, jwt_settings, make_user
) -> None:
    uow.users.get_by_email.return_value = make_user(is_verified=True)

    handler = RequestLoginCodeHandler(uow, email_sender, jwt_settings)
    before = datetime.now(UTC)
    await handler.handle(RequestLoginCodeCommand(email="user@example.com"))
    await asyncio.sleep(0)

    expires_at = uow.email_codes.create.call_args.args[0]["expires_at"]
    expected = timedelta(minutes=jwt_settings.pending_ttl_minutes)
    assert before + expected <= expires_at <= datetime.now(UTC) + expected


async def test_request_login_code_unverified_email(
    uow, email_sender, jwt_settings, make_user
) -> None:
    uow.users.get_by_email.return_value = make_user(is_verified=False)

    handler = RequestLoginCodeHandler(uow, email_sender, jwt_settings)
    with pytest.raises(LoginNotAllowedError):
        await handler.handle(RequestLoginCodeCommand(email="user@example.com"))

    uow.email_codes.create.assert_not_awaited()


async def test_request_login_code_success(
    uow, email_sender, jwt_settings, make_user
) -> None:
    uow.users.get_by_email.return_value = make_user(is_verified=True)

    handler = RequestLoginCodeHandler(uow, email_sender, jwt_settings)
    await handler.handle(RequestLoginCodeCommand(email="user@example.com"))
    await asyncio.sleep(0)
    await asyncio.sleep(0)

    uow.email_codes.create.assert_awaited_once()
    payload = uow.email_codes.create.call_args.args[0]
    assert payload["purpose"] == "login"
    assert payload["email"] == "user@example.com"
    email_sender.send_code.assert_awaited_once_with("user@example.com", payload["code"])


async def test_confirm_login_success(uow, code_settings, make_code, make_user) -> None:
    uow.email_codes.get_active.return_value = make_code(
        code="123456", purpose=EmailCodePurposeEnum.LOGIN
    )
    uow.users.get_by_email.return_value = make_user(is_verified=True)

    handler = ConfirmLoginHandler(uow, code_settings)
    user = await handler.handle(
        ConfirmLoginCommand(email="user@example.com", code="123456")
    )

    assert user.email == "user@example.com"
    uow.email_codes.update.assert_awaited_once()
    assert "used_at" in uow.email_codes.update.call_args.kwargs["obj_in"]


async def test_confirm_login_wrong_code_counts_attempt(
    uow, code_settings, make_code
) -> None:
    uow.email_codes.get_active.return_value = make_code(
        code="111111", purpose=EmailCodePurposeEnum.LOGIN, attempts=0
    )

    handler = ConfirmLoginHandler(uow, code_settings)
    with pytest.raises(InvalidEmailCodeError):
        await handler.handle(
            ConfirmLoginCommand(email="user@example.com", code="000000")
        )

    uow.email_codes.update.assert_awaited_once()
    assert uow.email_codes.update.call_args.kwargs["obj_in"] == {"attempts": 1}
    assert uow.email_codes.update.call_args.kwargs["auto_commit"] is True


async def test_confirm_login_exhausted_code_rejects_right_code(
    uow, code_settings, make_code
) -> None:
    uow.email_codes.get_active.return_value = make_code(
        code="123456",
        purpose=EmailCodePurposeEnum.LOGIN,
        attempts=code_settings.max_attempts,
    )

    handler = ConfirmLoginHandler(uow, code_settings)
    with pytest.raises(InvalidEmailCodeError):
        await handler.handle(
            ConfirmLoginCommand(email="user@example.com", code="123456")
        )

    uow.email_codes.update.assert_not_awaited()
    uow.users.get_by_email.assert_not_awaited()


async def test_confirm_login_no_active_code(uow, code_settings) -> None:
    uow.email_codes.get_active.return_value = None

    handler = ConfirmLoginHandler(uow, code_settings)
    with pytest.raises(InvalidEmailCodeError):
        await handler.handle(
            ConfirmLoginCommand(email="user@example.com", code="123456")
        )

    uow.email_codes.update.assert_not_awaited()
    uow.users.get_by_email.assert_not_awaited()


async def test_confirm_login_user_deleted_between_steps(
    uow, code_settings, make_code
) -> None:
    uow.email_codes.get_active.return_value = make_code(
        code="123456", purpose=EmailCodePurposeEnum.LOGIN
    )
    uow.users.get_by_email.return_value = None

    handler = ConfirmLoginHandler(uow, code_settings)
    with pytest.raises(InvalidEmailCodeError):
        await handler.handle(
            ConfirmLoginCommand(email="user@example.com", code="123456")
        )


async def test_confirm_login_user_unverified_between_steps(
    uow, code_settings, make_code, make_user
) -> None:
    uow.email_codes.get_active.return_value = make_code(
        code="123456", purpose=EmailCodePurposeEnum.LOGIN
    )
    uow.users.get_by_email.return_value = make_user(is_verified=False)

    handler = ConfirmLoginHandler(uow, code_settings)
    with pytest.raises(InvalidEmailCodeError):
        await handler.handle(
            ConfirmLoginCommand(email="user@example.com", code="123456")
        )
