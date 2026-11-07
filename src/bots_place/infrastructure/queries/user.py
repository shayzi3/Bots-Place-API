from bots_place.domain.entities.user import UserBaseModel
from bots_place.domain.queries import GetUserByIdQuery
from bots_place.infrastructure.repository import Model
from bots_place.infrastructure.repository.base import BaseUnitOfWork


class GetUserByIdHandler:
    def __init__(self, uow: BaseUnitOfWork) -> None:
        self._uow = uow

    async def handle(self, query: GetUserByIdQuery) -> UserBaseModel | None:
        return await self._uow.users.get(Model.id == query.user_id)
