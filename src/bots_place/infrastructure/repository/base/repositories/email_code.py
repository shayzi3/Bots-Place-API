from abc import abstractmethod

from bots_place.domain.entities.email_code import EmailCodeBaseModel

from .base import BaseRepository


class BaseEmailCodeRepository(BaseRepository[EmailCodeBaseModel]):
    @abstractmethod
    async def get_active(
        self, email: str, purpose: str
    ) -> EmailCodeBaseModel | None: ...
