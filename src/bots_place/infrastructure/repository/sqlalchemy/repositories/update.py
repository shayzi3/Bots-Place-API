from bots_place.domain.entities.update import UpdateBaseModel
from bots_place.infrastructure.repository.base.repositories.update import (
    BaseUpdateRepository,
)
from bots_place.infrastructure.repository.expressions import Model
from bots_place.infrastructure.repository.sqlalchemy.models.update import Update

from .base import SqlAlchemyBaseRepository


class UpdateRepository(
    SqlAlchemyBaseRepository[Update, UpdateBaseModel], BaseUpdateRepository
):
    model = Update
    entity = UpdateBaseModel

    async def get_unprocessed(self, limit: int = 100) -> list[UpdateBaseModel]:
        return await self.get_all(
            Model.processed.is_(False),
            order_by=Model.created_at.asc(),
            limit=limit,
        )

    async def get_by_chat(self, chat_id: int) -> list[UpdateBaseModel]:
        return await self.get_all(
            Model.chat_id == chat_id,
            order_by=Model.created_at.asc(),
        )
