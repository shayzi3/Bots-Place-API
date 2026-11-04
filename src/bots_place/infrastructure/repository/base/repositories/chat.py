from abc import abstractmethod

from bots_place.domain.entities.chat import ChatModel

from .base import BaseRepository


class BaseChatRepository(BaseRepository):
    @abstractmethod
    async def get_by_bot_and_user(
        self, bot_id: int, user_id: int
    ) -> ChatModel | None: ...

    @abstractmethod
    async def get_by_bot(self, bot_id: int) -> list[ChatModel]: ...
