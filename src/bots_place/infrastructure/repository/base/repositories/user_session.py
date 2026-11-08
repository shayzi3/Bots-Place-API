from abc import abstractmethod
from datetime import datetime

from bots_place.domain.entities.user_session import UserSessionBaseModel

from .base import BaseRepository


class BaseUserSessionRepository(BaseRepository[UserSessionBaseModel]):
    @abstractmethod
    async def revoke_all_for_user(
        self, user_id: int, revoked_at: datetime, auto_commit: bool = True
    ) -> None: ...
