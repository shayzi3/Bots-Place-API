from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ModelFieldExpression:
    field: str
    operator: str
    value: Any


@dataclass(frozen=True)
class ModelOrderExpression:
    field: str
    direction: str


class ModelField:
    def __init__(self, field: str) -> None:
        self.field = field

    def __lt__(self, other: Any) -> ModelFieldExpression:
        return ModelFieldExpression(self.field, "<", other)

    def __le__(self, other: Any) -> ModelFieldExpression:
        return ModelFieldExpression(self.field, "<=", other)

    def __eq__(self, other: object) -> ModelFieldExpression:  # type: ignore[override]
        return ModelFieldExpression(self.field, "==", other)

    def __ne__(self, other: object) -> ModelFieldExpression:  # type: ignore[override]
        return ModelFieldExpression(self.field, "!=", other)

    def __gt__(self, other: Any) -> ModelFieldExpression:
        return ModelFieldExpression(self.field, ">", other)

    def __ge__(self, other: Any) -> ModelFieldExpression:
        return ModelFieldExpression(self.field, ">=", other)

    def in_(self, values: Any) -> ModelFieldExpression:
        return ModelFieldExpression(self.field, "in", values)

    def is_(self, value: Any) -> ModelFieldExpression:
        return ModelFieldExpression(self.field, "is", value)

    def like(self, value: Any) -> ModelFieldExpression:
        return ModelFieldExpression(self.field, "like", value)

    def asc(self) -> ModelOrderExpression:
        return ModelOrderExpression(self.field, "asc")

    def desc(self) -> ModelOrderExpression:
        return ModelOrderExpression(self.field, "desc")

    def __hash__(self) -> int:
        return hash(self.field)


class ModelMeta(type):
    def __getattr__(cls, name: str) -> ModelField:
        return ModelField(field=name)


class Model(metaclass=ModelMeta): ...
