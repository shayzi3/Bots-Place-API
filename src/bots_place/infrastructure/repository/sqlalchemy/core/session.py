from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from bots_place.config.env import settings

engine = create_async_engine(settings.database.url)

session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
