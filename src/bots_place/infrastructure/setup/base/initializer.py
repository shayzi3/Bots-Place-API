from abc import ABC, abstractmethod


class BaseDatabaseInitializer(ABC):
    """Technology-agnostic database schema initializer."""

    @abstractmethod
    async def create_all(self) -> None: ...
