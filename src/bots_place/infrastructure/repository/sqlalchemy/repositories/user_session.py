from datetime import datetime

from sqlalchemy import update

from bots_place.domain.entities.user_session import UserSessionBaseModel
from bots_place.infrastructure.repository.base.repositories.user_session import (
    BaseUserSessionRepository,
)
from bots_place.infrastructure.repository.sqlalchemy.models.user_session import (
    UserSession,
)

from .base import SqlAlchemyBaseRepository


class UserSessionRepository(
    SqlAlchemyBaseRepository[UserSession, UserSessionBaseModel],
    BaseUserSessionRepository,
):
    model = UserSession
    entity = UserSessionBaseModel

    async def revoke_all_for_user(
        self, user_id: int, revoked_at: datetime, auto_commit: bool = True
    ) -> None:
        stmt = (
            update(UserSession)
            .where(
                UserSession.user_id == user_id,
                UserSession.revoked_at.is_(None),
            )
            .values(revoked_at=revoked_at)
        )
        await self.session.execute(stmt)
        if auto_commit:
            await self.session.commit()
        else:
            await self.session.flush()
