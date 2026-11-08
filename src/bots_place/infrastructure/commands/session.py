from datetime import UTC, datetime, timedelta

from bots_place.app.security.sessions import hash_session_token, new_session_token
from bots_place.config.env import JwtSettings
from bots_place.domain.commands import CreateSessionCommand, RevokeSessionCommand
from bots_place.infrastructure.repository import Model
from bots_place.infrastructure.repository.base import BaseUnitOfWork


class CreateSessionHandler:
    def __init__(self, uow: BaseUnitOfWork, jwt_settings: JwtSettings) -> None:
        self._uow = uow
        self._jwt_settings = jwt_settings

    async def handle(self, command: CreateSessionCommand) -> str:
        token = new_session_token()
        await self._uow.sessions.create(
            {
                "user_id": command.user_id,
                "token_hash": hash_session_token(token),
                "expires_at": datetime.now(UTC)
                + timedelta(minutes=self._jwt_settings.access_ttl_minutes),
            },
            auto_commit=True,
        )
        return token


class RevokeSessionHandler:
    def __init__(self, uow: BaseUnitOfWork) -> None:
        self._uow = uow

    async def handle(self, command: RevokeSessionCommand) -> None:
        await self._uow.sessions.update(
            Model.token_hash == hash_session_token(command.token),
            obj_in={"revoked_at": datetime.now(UTC)},
            auto_commit=True,
        )
