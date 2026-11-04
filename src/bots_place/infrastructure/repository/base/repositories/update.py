from abc import abstractmethod

from bots_place.domain.entities.update import UpdateBaseModel

from .base import BaseRepository


class BaseUpdateRepository(BaseRepository[UpdateBaseModel]):
    @abstractmethod
    async def get_unprocessed(self, limit: int = 100) -> list[UpdateBaseModel]: ...

    @abstractmethod
    async def get_by_chat(self, chat_id: int) -> list[UpdateBaseModel]: ...
