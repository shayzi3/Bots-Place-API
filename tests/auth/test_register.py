import asyncio

import pytest

from bots_place.domain.commands import (
    ConfirmRegistrationCommand,
    RegisterUserCommand,
)
from bots_place.domain.entities.email_code import EmailCodePurposeEnum
from bots_place.domain.exceptions.user import (
    EmailAlreadyExistsError,
    InvalidEmailCodeError,
)
from bots_place.infrastructure.commands.register import (
    ConfirmRegistrationHandler,
    RegisterUserHandler,
)


async def test_register_new_email_creates_user_code_and_sends(
    uow, email_sender, jwt_settings
) -> None:
    uow.users.get_by_email.return_value = None

    handler = RegisterUserHandler(uow, email_sender, jwt_settings)
    await handler.handle(RegisterUserCommand(email="new@example.com", username="new"))
    await asyncio.sleep(0)
    await asyncio.sleep(0)

    uow.users.create.assert_awaited_once()
    created = uow.users.create.call_args.args[0]
    assert created["email"] == "new@example.com"
    assert created["auth_from"] == "basic"
    assert created["is_verified"] is False

    uow.email_codes.create.assert_awaited_once()
    code_payload = uow.email_codes.create.call_args.args[0]
    assert code_payload["purpose"] == "registration"
    assert len(code_payload["code"]) == 6
    assert code_payload["code"].isdigit()

    uow.commit.assert_awaited_once()
    email_sender.send_code.assert_awaited_once_with(
        "new@example.com", code_payload["code"]
    )


async def test_register_verified_email_raises(
    uow, email_sender, jwt_settings, make_user
) -> None:
    uow.users.get_by_email.return_value = make_user(is_verified=True)

    handler = RegisterUserHandler(uow, email_sender, jwt_settings)
    with pytest.raises(EmailAlreadyExistsError):
        await handler.handle(
            RegisterUserCommand(email="user@example.com", username="user")
        )

    uow.users.create.assert_not_awaited()
    uow.email_codes.create.assert_not_awaited()
    email_sender.send_code.assert_not_awaited()


async def test_register_unverified_existing_resends_code(
    uow, email_sender, jwt_settings, make_user
) -> None:
    uow.users.get_by_email.return_value = make_user(is_verified=False)

    handler = RegisterUserHandler(uow, email_sender, jwt_settings)
    await handler.handle(RegisterUserCommand(email="user@example.com", username="user"))
    await asyncio.sleep(0)
    await asyncio.sleep(0)

    uow.users.create.assert_not_awaited()
    uow.email_codes.create.assert_awaited_once()
    email_sender.send_code.assert_awaited_once()


async def test_confirm_registration_success(
    uow, code_settings, make_code, make_user
) -> None:
    uow.email_codes.get_active.return_value = make_code(
        code="123456", purpose=EmailCodePurposeEnum.REGISTRATION
    )
    uow.users.update.return_value = make_user(is_verified=True)

    handler = ConfirmRegistrationHandler(uow, code_settings)
    user = await handler.handle(
        ConfirmRegistrationCommand(email="user@example.com", code="123456")
    )

    assert user.is_verified is True
    uow.email_codes.update.assert_awaited_once()
    assert "used_at" in uow.email_codes.update.call_args.kwargs["obj_in"]
    uow.users.update.assert_awaited_once()
    assert uow.users.update.call_args.kwargs["obj_in"] == {"is_verified": True}


async def test_confirm_registration_wrong_code_counts_attempt(
    uow, code_settings, make_code
) -> None:
    uow.email_codes.get_active.return_value = make_code(code="111111", attempts=2)

    handler = ConfirmRegistrationHandler(uow, code_settings)
    with pytest.raises(InvalidEmailCodeError):
        await handler.handle(
            ConfirmRegistrationCommand(email="user@example.com", code="222222")
        )

    uow.email_codes.update.assert_awaited_once()
    assert uow.email_codes.update.call_args.kwargs["obj_in"] == {"attempts": 3}
    assert uow.email_codes.update.call_args.kwargs["auto_commit"] is True
    uow.users.update.assert_not_awaited()


async def test_confirm_registration_exhausted_code_rejects_right_code(
    uow, code_settings, make_code
) -> None:
    uow.email_codes.get_active.return_value = make_code(
        code="123456", attempts=code_settings.max_attempts
    )

    handler = ConfirmRegistrationHandler(uow, code_settings)
    with pytest.raises(InvalidEmailCodeError):
        await handler.handle(
            ConfirmRegistrationCommand(email="user@example.com", code="123456")
        )

    uow.email_codes.update.assert_not_awaited()
    uow.users.update.assert_not_awaited()


async def test_confirm_registration_user_missing_after_update(
    uow, code_settings, make_code
) -> None:
    uow.email_codes.get_active.return_value = make_code(
        code="123456", purpose=EmailCodePurposeEnum.REGISTRATION
    )
    uow.users.update.return_value = None

    handler = ConfirmRegistrationHandler(uow, code_settings)
    with pytest.raises(InvalidEmailCodeError):
        await handler.handle(
            ConfirmRegistrationCommand(email="user@example.com", code="123456")
        )


async def test_confirm_registration_no_active_code(uow, code_settings) -> None:
    uow.email_codes.get_active.return_value = None

    handler = ConfirmRegistrationHandler(uow, code_settings)
    with pytest.raises(InvalidEmailCodeError):
        await handler.handle(
            ConfirmRegistrationCommand(email="user@example.com", code="123456")
        )
