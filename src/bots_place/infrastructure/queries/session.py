from datetime import UTC, datetime

from bots_place.app.security.sessions import hash_session_token
from bots_place.domain.entities.user import UserBaseModel
from bots_place.domain.queries import GetUserBySessionQuery
from bots_place.infrastructure.repository import Model
from bots_place.infrastructure.repository.base import BaseUnitOfWork


class GetUserBySessionHandler:
    def __init__(self, uow: BaseUnitOfWork) -> None:
        self._uow = uow

    async def handle(self, query: GetUserBySessionQuery) -> UserBaseModel | None:
        session = await self._uow.sessions.get(
            Model.token_hash == hash_session_token(query.token),
            Model.revoked_at.is_(None),
            Model.expires_at > datetime.now(UTC),
        )
        if session is None:
            return None
        return await self._uow.users.get(Model.id == session.user_id)
