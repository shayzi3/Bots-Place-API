from bots_place.domain.entities.bot import BotModel
from bots_place.infrastructure.repository.base.repositories.bot import (
    BaseBotRepository,
)
from bots_place.infrastructure.repository.expressions import Model
from bots_place.infrastructure.repository.sqlalchemy.models.bot import Bot

from .base import SqlAlchemyBaseRepository


class BotRepository(SqlAlchemyBaseRepository[Bot, BotModel], BaseBotRepository):
    model = Bot
    entity = BotModel

    async def get_by_token(self, token: str) -> BotModel | None:
        return await self.get(Model.token == token)

    async def get_by_owner(self, owner_id: int) -> list[BotModel]:
        return await self.get_all(Model.owner_id == owner_id)
