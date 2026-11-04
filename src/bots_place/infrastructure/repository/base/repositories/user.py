from abc import abstractmethod

from bots_place.domain.entities.user import UserBaseModel

from .base import BaseRepository


class BaseUserRepository(BaseRepository[UserBaseModel]):
    @abstractmethod
    async def get_by_email(self, email: str) -> UserBaseModel | None: ...

    @abstractmethod
    async def email_exists(self, email: str) -> bool: ...
