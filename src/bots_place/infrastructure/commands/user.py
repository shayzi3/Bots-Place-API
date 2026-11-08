import asyncio
import math
from datetime import UTC, datetime, timedelta
from uuid import UUID

from bots_place.app.security.codes import generate_code
from bots_place.app.tasks.email import EmailSender
from bots_place.config.env import CodeSettings, JwtSettings
from bots_place.domain.commands import (
    ChangeUserEmailCommand,
    ChangeUsernameCommand,
    ConfirmEmailChangeCommand,
    UseEmailChangeLinkCommand,
)
from bots_place.domain.entities.email_change_request import (
    EmailChangeRequestBaseModel,
)
from bots_place.domain.entities.email_code import EmailCodePurposeEnum
from bots_place.domain.entities.user import UserBaseModel
from bots_place.domain.exceptions.user import (
    EmailAlreadyExistsError,
    EmailChangeLinkInvalidError,
    InvalidEmailCodeError,
    ResendCooldownError,
    UserNotFoundError,
)
from bots_place.infrastructure.repository import Model
from bots_place.infrastructure.repository.base import BaseUnitOfWork

EMAIL_CHANGE_COOLDOWN_SECONDS = 300


class ChangeUsernameHandler:
    def __init__(self, uow: BaseUnitOfWork) -> None:
        self._uow = uow

    async def handle(self, command: ChangeUsernameCommand) -> UserBaseModel:
        user = await self._uow.users.update(
            Model.id == command.user_id,
            obj_in={"username": command.new_username},
            auto_commit=True,
        )
        if user is None:
            raise UserNotFoundError(command.user_id)
        return user


class RequestEmailChangeHandler:
    def __init__(
        self,
        uow: BaseUnitOfWork,
        email_sender: EmailSender,
        jwt_settings: JwtSettings,
    ) -> None:
        self._uow = uow
        self._email_sender = email_sender
        self._jwt_settings = jwt_settings

    async def handle(self, command: ChangeUserEmailCommand) -> None:
        user = await self._uow.users.get(Model.id == command.user_id)
        if user is None:
            raise UserNotFoundError(command.user_id)
        if await self._uow.users.email_exists(command.new_email):
            raise EmailAlreadyExistsError(command.new_email)

        now = datetime.now(UTC)
        latest = await self._uow.email_change_requests.get_latest_for_user(
            command.user_id
        )
        if latest is not None:
            elapsed = (now - latest.created_at).total_seconds()
            remaining = EMAIL_CHANGE_COOLDOWN_SECONDS - elapsed
            if remaining > 0:
                raise ResendCooldownError(math.ceil(remaining))

        request = await self._uow.email_change_requests.create(
            {
                "user_id": command.user_id,
                "new_email": command.new_email,
                "expires_at": now
                + timedelta(minutes=self._jwt_settings.pending_ttl_minutes),
            },
            auto_commit=True,
        )

        link = f"{command.link_url}?token={request.id}"
        asyncio.create_task(self._email_sender.send_link(user.email, link))


class UseEmailChangeLinkHandler:
    def __init__(
        self,
        uow: BaseUnitOfWork,
        email_sender: EmailSender,
        jwt_settings: JwtSettings,
    ) -> None:
        self._uow = uow
        self._email_sender = email_sender
        self._jwt_settings = jwt_settings

    async def handle(
        self, command: UseEmailChangeLinkCommand
    ) -> EmailChangeRequestBaseModel:
        try:
            request_id = UUID(command.token)
        except ValueError as exc:
            raise EmailChangeLinkInvalidError from exc

        request = await self._uow.email_change_requests.get(Model.id == request_id)
        now = datetime.now(UTC)
        if request is None or request.used_at is not None or request.expires_at <= now:
            raise EmailChangeLinkInvalidError

        await self._uow.email_change_requests.update(
            Model.id == request.id,
            obj_in={"used_at": now},
            auto_commit=False,
        )
        code = generate_code()
        await self._uow.email_codes.create(
            {
                "email": request.new_email,
                "code": code,
                "purpose": EmailCodePurposeEnum.CHANGE_EMAIL.value,
                "expires_at": now
                + timedelta(minutes=self._jwt_settings.pending_ttl_minutes),
            },
            auto_commit=False,
        )
        await self._uow.commit()

        asyncio.create_task(self._email_sender.send_code(request.new_email, code))
        return request


class ConfirmEmailChangeHandler:
    def __init__(self, uow: BaseUnitOfWork, code_settings: CodeSettings) -> None:
        self._uow = uow
        self._code_settings = code_settings

    async def handle(self, command: ConfirmEmailChangeCommand) -> UserBaseModel:
        code = await self._uow.email_codes.get_active(
            command.email, EmailCodePurposeEnum.CHANGE_EMAIL.value
        )
        if code is None or code.attempts >= self._code_settings.max_attempts:
            raise InvalidEmailCodeError
        if code.code != command.code:
            await self._uow.email_codes.update(
                Model.id == code.id,
                obj_in={"attempts": code.attempts + 1},
                auto_commit=True,
            )
            raise InvalidEmailCodeError

        if await self._uow.users.email_exists(command.email):
            raise EmailAlreadyExistsError(command.email)

        await self._uow.email_codes.update(
            Model.id == code.id,
            obj_in={"used_at": datetime.now(UTC)},
            auto_commit=False,
        )
        await self._uow.sessions.revoke_all_for_user(
            command.user_id, datetime.now(UTC), auto_commit=False
        )
        user = await self._uow.users.update(
            Model.id == command.user_id,
            obj_in={"email": command.email},
            auto_commit=True,
        )
        if user is None:
            raise UserNotFoundError(command.user_id)
        return user
