from bots_place.domain.entities.user import UserBaseModel
from bots_place.infrastructure.repository.base.repositories.user import (
    BaseUserRepository,
)
from bots_place.infrastructure.repository.expressions import Model
from bots_place.infrastructure.repository.sqlalchemy.models.user import User

from .base import SqlAlchemyBaseRepository


class UserRepository(SqlAlchemyBaseRepository[User, UserBaseModel], BaseUserRepository):
    model = User
    entity = UserBaseModel

    async def get_by_email(self, email: str) -> UserBaseModel | None:
        return await self.get(Model.email == email)

    async def email_exists(self, email: str) -> bool:
        return await self.get_by_email(email) is not None
