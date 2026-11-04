from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Any

from pydantic import BaseModel

from bots_place.infrastructure.repository.expressions import (
    ModelFieldExpression,
    ModelOrderExpression,
)


class BaseRepository(ABC):
    """Technology-agnostic repository contract."""

    @abstractmethod
    async def get(self, *where: ModelFieldExpression) -> Any: ...

    @abstractmethod
    async def get_all(
        self,
        *where: ModelFieldExpression,
        order_by: ModelOrderExpression | None = None,
        offset: int | None = None,
        limit: int | None = None,
    ) -> list[Any]: ...

    @abstractmethod
    async def create(
        self,
        obj_in: BaseModel | Mapping[str, Any],
        auto_commit: bool = True,
    ) -> Any: ...

    @abstractmethod
    async def update(
        self,
        *where: ModelFieldExpression,
        obj_in: BaseModel | Mapping[str, Any],
        auto_commit: bool = True,
    ) -> Any | None: ...

    @abstractmethod
    async def update_by_id(
        self,
        model_id: int,
        obj_in: BaseModel | Mapping[str, Any],
        auto_commit: bool = True,
    ) -> Any | None: ...

    @abstractmethod
    async def delete(
        self, *where: ModelFieldExpression, auto_commit: bool = True
    ) -> int: ...

    @abstractmethod
    async def delete_by_id(self, model_id: int, auto_commit: bool = True) -> bool: ...
