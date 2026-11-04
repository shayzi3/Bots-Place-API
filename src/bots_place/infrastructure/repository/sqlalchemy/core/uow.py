from types import TracebackType
from typing import Self

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from bots_place.infrastructure.repository.base.core.uow import BaseUnitOfWork
from bots_place.infrastructure.repository.sqlalchemy.repositories import (
    BotRepository,
    ChatRepository,
    EmailCodeRepository,
    UpdateRepository,
    UserRepository,
)


class UnitOfWork(BaseUnitOfWork):
    """Creates a session and exposes every repository bound to it.

    Usage:
        async with UnitOfWork(session_factory) as uow:
            user = await uow.users.create(...)
            await uow.commit()
    """

    users: UserRepository
    email_codes: EmailCodeRepository
    bots: BotRepository
    chats: ChatRepository
    updates: UpdateRepository

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory
        self._session: AsyncSession | None = None

    async def __aenter__(self) -> Self:
        session = self._session_factory()
        self._session = session

        self.users = UserRepository(session)
        self.email_codes = EmailCodeRepository(session)
        self.bots = BotRepository(session)
        self.chats = ChatRepository(session)
        self.updates = UpdateRepository(session)

        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        session = self._session
        if session is None:
            return

        try:
            if exc_type is not None:
                await session.rollback()
        finally:
            await session.close()
            self._session = None

    @property
    def session(self) -> AsyncSession:
        if self._session is None:
            raise RuntimeError("UnitOfWork is not active. Use 'async with'.")
        return self._session

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()
