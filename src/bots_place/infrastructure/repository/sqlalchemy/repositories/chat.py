from bots_place.domain.entities.chat import ChatModel
from bots_place.infrastructure.repository.base.repositories.chat import (
    BaseChatRepository,
)
from bots_place.infrastructure.repository.expressions import Model
from bots_place.infrastructure.repository.sqlalchemy.models.chat import Chat

from .base import SqlAlchemyBaseRepository


class ChatRepository(SqlAlchemyBaseRepository[Chat, ChatModel], BaseChatRepository):
    model = Chat
    entity = ChatModel

    async def get_by_bot_and_user(self, bot_id: int, user_id: int) -> ChatModel | None:
        return await self.get(Model.bot_id == bot_id, Model.user_id == user_id)

    async def get_by_bot(self, bot_id: int) -> list[ChatModel]:
        return await self.get_all(Model.bot_id == bot_id)
