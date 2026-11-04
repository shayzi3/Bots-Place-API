import asyncio
from datetime import UTC, datetime, timedelta

from bots_place.app.security.codes import generate_code
from bots_place.app.tasks.email import EmailSender
from bots_place.config.env import JwtSettings
from bots_place.domain.commands import ConfirmLoginCommand, RequestLoginCodeCommand
from bots_place.domain.entities.email_code import EmailCodePurposeEnum
from bots_place.domain.entities.user import UserBaseModel
from bots_place.domain.exceptions.user import (
    InvalidEmailCodeError,
    LoginNotAllowedError,
)
from bots_place.infrastructure.repository import Model
from bots_place.infrastructure.repository.base import BaseUnitOfWork


class RequestLoginCodeHandler:
    def __init__(
        self,
        uow: BaseUnitOfWork,
        email_sender: EmailSender,
        jwt_settings: JwtSettings,
    ) -> None:
        self._uow = uow
        self._email_sender = email_sender
        self._jwt_settings = jwt_settings

    async def handle(self, command: RequestLoginCodeCommand) -> None:
        user = await self._uow.users.get_by_email(command.email)
        if user is None or not user.is_verified:
            raise LoginNotAllowedError(command.email)

        code = generate_code()
        expires_at = datetime.now(UTC) + timedelta(
            minutes=self._jwt_settings.pending_ttl_minutes
        )
        await self._uow.email_codes.create(
            {
                "email": command.email,
                "code": code,
                "purpose": EmailCodePurposeEnum.LOGIN.value,
                "expires_at": expires_at,
            },
            auto_commit=True,
        )

        asyncio.create_task(self._email_sender.send_code(command.email, code))


class ConfirmLoginHandler:
    def __init__(self, uow: BaseUnitOfWork) -> None:
        self._uow = uow

    async def handle(self, command: ConfirmLoginCommand) -> UserBaseModel:
        code = await self._uow.email_codes.get_active(
            command.email, EmailCodePurposeEnum.LOGIN.value
        )
        if code is None or code.code != command.code:
            raise InvalidEmailCodeError

        await self._uow.email_codes.update(
            Model.id == code.id,
            obj_in={"used_at": datetime.now(UTC)},
            auto_commit=True,
        )

        user = await self._uow.users.get_by_email(command.email)
        if user is None or not user.is_verified:
            raise InvalidEmailCodeError
        return user
