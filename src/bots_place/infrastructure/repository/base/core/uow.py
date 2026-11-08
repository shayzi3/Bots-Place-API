from abc import ABC, abstractmethod
from types import TracebackType
from typing import Self

from ..repositories import (
    BaseBotRepository,
    BaseChatRepository,
    BaseEmailChangeRequestRepository,
    BaseEmailCodeRepository,
    BaseUpdateRepository,
    BaseUserRepository,
    BaseUserSessionRepository,
)


class BaseUnitOfWork(ABC):
    """Technology-agnostic unit of work contract."""

    users: BaseUserRepository
    email_codes: BaseEmailCodeRepository
    email_change_requests: BaseEmailChangeRequestRepository
    sessions: BaseUserSessionRepository
    bots: BaseBotRepository
    chats: BaseChatRepository
    updates: BaseUpdateRepository

    @abstractmethod
    async def __aenter__(self) -> Self: ...

    @abstractmethod
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None: ...

    @abstractmethod
    async def commit(self) -> None: ...

    @abstractmethod
    async def rollback(self) -> None: ...
