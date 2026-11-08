import asyncio
import math
from datetime import UTC, datetime, timedelta

from bots_place.app.security.codes import generate_code
from bots_place.app.tasks.email import EmailSender
from bots_place.config.env import CodeSettings, JwtSettings
from bots_place.domain.commands import ResendCodeCommand
from bots_place.domain.entities.email_code import EmailCodePurposeEnum
from bots_place.domain.exceptions.user import (
    ResendCooldownError,
    ResendNotAllowedError,
)
from bots_place.infrastructure.repository import Model
from bots_place.infrastructure.repository.base import BaseUnitOfWork


class ResendCodeHandler:
    def __init__(
        self,
        uow: BaseUnitOfWork,
        email_sender: EmailSender,
        code_settings: CodeSettings,
        jwt_settings: JwtSettings,
    ) -> None:
        self._uow = uow
        self._email_sender = email_sender
        self._code_settings = code_settings
        self._jwt_settings = jwt_settings

    async def handle(self, command: ResendCodeCommand) -> None:
        if command.purpose is not EmailCodePurposeEnum.CHANGE_EMAIL:
            user = await self._uow.users.get_by_email(command.email)
            is_login = command.purpose is EmailCodePurposeEnum.LOGIN
            if user is None or user.is_verified != is_login:
                raise ResendNotAllowedError(command.email)

        now = datetime.now(UTC)
        active = await self._uow.email_codes.get_active(
            command.email, command.purpose.value
        )
        if active is not None:
            elapsed = (now - active.created_at).total_seconds()
            remaining = self._code_settings.resend_cooldown_seconds - elapsed
            if remaining > 0:
                raise ResendCooldownError(math.ceil(remaining))
            await self._uow.email_codes.update(
                Model.id == active.id,
                obj_in={"revoked": True},
                auto_commit=False,
            )

        code = generate_code()
        await self._uow.email_codes.create(
            {
                "email": command.email,
                "code": code,
                "purpose": command.purpose.value,
                "expires_at": now
                + timedelta(minutes=self._jwt_settings.pending_ttl_minutes),
            },
            auto_commit=False,
        )
        await self._uow.commit()

        asyncio.create_task(self._email_sender.send_code(command.email, code))
