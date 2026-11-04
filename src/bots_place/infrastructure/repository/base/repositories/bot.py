from abc import abstractmethod

from bots_place.domain.entities.bot import BotModel

from .base import BaseRepository


class BaseBotRepository(BaseRepository[BotModel]):
    @abstractmethod
    async def get_by_token(self, token: str) -> BotModel | None: ...

    @abstractmethod
    async def get_by_owner(self, owner_id: int) -> list[BotModel]: ...
