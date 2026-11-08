from abc import abstractmethod

from bots_place.domain.entities.email_change_request import (
    EmailChangeRequestBaseModel,
)

from .base import BaseRepository


class BaseEmailChangeRequestRepository(BaseRepository[EmailChangeRequestBaseModel]):
    @abstractmethod
    async def get_latest_for_user(
        self, user_id: int
    ) -> EmailChangeRequestBaseModel | None: ...
