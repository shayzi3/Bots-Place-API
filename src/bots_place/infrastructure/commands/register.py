import asyncio
import secrets
from datetime import UTC, datetime, timedelta

from bots_place.app.tasks.email import EmailSender
from bots_place.config.env import JwtSettings
from bots_place.domain.commands import (
    ConfirmRegistrationCommand,
    RegisterUserCommand,
)
from bots_place.domain.entities.email_code import EmailCodePurposeEnum
from bots_place.domain.entities.user import UserAuthEnum, UserBaseModel
from bots_place.domain.exceptions.user import (
    EmailAlreadyExistsError,
    InvalidEmailCodeError,
)
from bots_place.infrastructure.repository import Model
from bots_place.infrastructure.repository.base import BaseUnitOfWork


def generate_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


class RegisterUserHandler:
    def __init__(
        self,
        uow: BaseUnitOfWork,
        email_sender: EmailSender,
        jwt_settings: JwtSettings,
    ) -> None:
        self._uow = uow
        self._email_sender = email_sender
        self._jwt_settings = jwt_settings

    async def handle(self, command: RegisterUserCommand) -> None:
        user = await self._uow.users.get_by_email(command.email)
        if user is None:
            await self._uow.users.create(
                {
                    "email": command.email,
                    "username": command.username,
                    "auth_from": UserAuthEnum.BASIC.value,
                    "is_verified": False,
                },
                auto_commit=False,
            )
        elif user.is_verified is True:
            raise EmailAlreadyExistsError(command.email)

        code = generate_code()
        expires_at = datetime.now(UTC) + timedelta(
            minutes=self._jwt_settings.pending_ttl_minutes
        )
        await self._uow.email_codes.create(
            {
                "email": command.email,
                "code": code,
                "purpose": EmailCodePurposeEnum.REGISTRATION.value,
                "expires_at": expires_at,
            },
            auto_commit=False,
        )
        await self._uow.commit()

        asyncio.create_task(self._email_sender.send_code(command.email, code))


class ConfirmRegistrationHandler:
    def __init__(self, uow: BaseUnitOfWork) -> None:
        self._uow = uow

    async def handle(self, command: ConfirmRegistrationCommand) -> UserBaseModel:
        code = await self._uow.email_codes.get_active(
            command.email, EmailCodePurposeEnum.REGISTRATION.value
        )
        if code is None or code.code != command.code:
            raise InvalidEmailCodeError

        await self._uow.email_codes.update(
            Model.id == code.id,
            obj_in={"used_at": datetime.now(UTC)},
            auto_commit=False,
        )
        user = await self._uow.users.update(
            Model.email == command.email,
            obj_in={"is_verified": True},
            auto_commit=True,
        )
        if user is None:
            raise InvalidEmailCodeError
        return user
