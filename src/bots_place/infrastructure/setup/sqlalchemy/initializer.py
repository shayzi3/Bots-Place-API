from sqlalchemy.ext.asyncio import AsyncEngine

from bots_place.infrastructure.repository.sqlalchemy.models import Base
from bots_place.infrastructure.setup.base.initializer import BaseDatabaseInitializer


class SqlAlchemyDatabaseInitializer(BaseDatabaseInitializer):
    def __init__(self, engine: AsyncEngine) -> None:
        self._engine = engine

    async def create_all(self) -> None:
        async with self._engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
