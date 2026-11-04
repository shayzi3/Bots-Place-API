import logging
from collections.abc import AsyncGenerator, Iterable, Mapping
from contextlib import asynccontextmanager
from typing import Any, cast

from pydantic import BaseModel
from sqlalchemy import delete, insert, select, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from bots_place.infrastructure.repository.base.repositories.base import (
    BaseRepository,
)
from bots_place.infrastructure.repository.expressions import (
    Model,
    ModelFieldExpression,
    ModelOrderExpression,
)
from bots_place.infrastructure.repository.sqlalchemy.core.expressions import (
    build_conditions,
    build_order_by,
)
from bots_place.infrastructure.repository.sqlalchemy.models.base import Base

logger = logging.getLogger(__name__)


class SqlAlchemyBaseRepository[ModelType: Base, EntityType: BaseModel](
    BaseRepository[EntityType]
):
    model: type[ModelType]
    entity: type[EntityType]

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @staticmethod
    def _as_dict(obj_in: BaseModel | Mapping[str, Any]) -> dict[str, Any]:
        if isinstance(obj_in, BaseModel):
            return obj_in.model_dump(exclude_unset=True)
        return dict(obj_in)

    def _to_entity(self, instance: ModelType) -> EntityType:
        return self.entity.model_validate(instance, from_attributes=True)

    def _to_entities(self, instances: Iterable[ModelType]) -> list[EntityType]:
        return [self._to_entity(instance) for instance in instances]

    @asynccontextmanager
    async def _handle_db_errors(self) -> AsyncGenerator[None]:
        try:
            yield
        except IntegrityError:
            await self.session.rollback()
            logger.exception("Integrity error in %s", self.model.__tablename__)
            raise
        except SQLAlchemyError:
            await self.session.rollback()
            logger.exception("Database error in %s", self.model.__tablename__)
            raise

    async def get(self, *where: ModelFieldExpression) -> EntityType | None:
        stmt = select(self.model)
        if where:
            stmt = stmt.where(*build_conditions(self.model, *where))

        result = await self.session.execute(stmt)
        instance = result.scalar_one_or_none()
        return self._to_entity(instance) if instance is not None else None

    async def get_all(
        self,
        *where: ModelFieldExpression,
        order_by: ModelOrderExpression | None = None,
        offset: int | None = None,
        limit: int | None = None,
    ) -> list[EntityType]:
        stmt = select(self.model)
        if where:
            stmt = stmt.where(*build_conditions(self.model, *where))
        if order_by is not None:
            stmt = stmt.order_by(*build_order_by(self.model, [order_by]))
        if offset is not None:
            stmt = stmt.offset(offset)
        if limit is not None:
            stmt = stmt.limit(limit)

        result = await self.session.execute(stmt)
        return self._to_entities(result.scalars().all())

    async def create(
        self,
        obj_in: BaseModel | Mapping[str, Any],
        auto_commit: bool = True,
    ) -> EntityType:
        data = self._as_dict(obj_in)

        async with self._handle_db_errors():
            stmt = insert(self.model).values(**data).returning(self.model)
            result = await self.session.execute(stmt)
            instance = result.scalar_one()

            if auto_commit:
                await self.session.commit()
                await self.session.refresh(instance)
            else:
                await self.session.flush()

            return self._to_entity(instance)

    async def update(
        self,
        *where: ModelFieldExpression,
        obj_in: BaseModel | Mapping[str, Any],
        auto_commit: bool = True,
    ) -> EntityType | None:
        if not where:
            raise ValueError(f"Cannot update {self.model.__name__} without conditions")

        data = self._as_dict(obj_in)

        async with self._handle_db_errors():
            stmt = (
                update(self.model)
                .where(*build_conditions(self.model, *where))
                .values(**data)
                .returning(self.model)
            )
            result = await self.session.execute(stmt)
            instance = result.scalar_one_or_none()

            if auto_commit:
                await self.session.commit()
                if instance is not None:
                    await self.session.refresh(instance)
            else:
                await self.session.flush()

            return self._to_entity(instance) if instance is not None else None

    async def update_by_id(
        self,
        model_id: int,
        obj_in: BaseModel | Mapping[str, Any],
        auto_commit: bool = True,
    ) -> EntityType | None:
        return await self.update(
            Model.id == model_id,
            obj_in=obj_in,
            auto_commit=auto_commit,
        )

    async def delete(
        self,
        *where: ModelFieldExpression,
        auto_commit: bool = True,
    ) -> int:
        if not where:
            raise ValueError(
                f"Cannot delete from {self.model.__name__} without conditions"
            )

        async with self._handle_db_errors():
            stmt = delete(self.model).where(*build_conditions(self.model, *where))
            result = await self.session.execute(stmt)

            if auto_commit:
                await self.session.commit()
            else:
                await self.session.flush()

            return cast(CursorResult[Any], result).rowcount

    async def delete_by_id(self, model_id: int, auto_commit: bool = True) -> bool:
        deleted = await self.delete(Model.id == model_id, auto_commit=auto_commit)
        return deleted > 0
