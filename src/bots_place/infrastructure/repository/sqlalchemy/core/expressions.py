from collections.abc import Iterable
from typing import Any

from sqlalchemy.sql.elements import ColumnElement

from bots_place.domain.exceptions.expressions import (
    UnknownFieldError,
    UnknownOperatorError,
)
from bots_place.infrastructure.repository.expressions import (
    ModelFieldExpression,
    ModelOrderExpression,
)
from bots_place.infrastructure.repository.sqlalchemy.models.base import Base


def _resolve_column(model: type[Base], field: str) -> Any:
    column = getattr(model, field, None)
    if column is None:
        raise UnknownFieldError(model.__name__, field)
    return column


def _apply_operator(column: Any, operator: str, value: Any) -> ColumnElement[bool]:
    match operator:
        case "<":
            return column < value
        case "<=":
            return column <= value
        case "==":
            return column == value
        case "!=":
            return column != value
        case ">":
            return column > value
        case ">=":
            return column >= value
        case "in":
            return column.in_(value)
        case "is":
            return column.is_(value)
        case "like":
            return column.like(value)
        case _:
            raise UnknownOperatorError(operator)


def build_condition(
    model: type[Base], expression: ModelFieldExpression
) -> ColumnElement[bool]:
    column = _resolve_column(model, expression.field)
    return _apply_operator(column, expression.operator, expression.value)


def build_conditions(
    model: type[Base], *expressions: ModelFieldExpression
) -> list[ColumnElement[bool]]:
    return [build_condition(model, expression) for expression in expressions]


def build_order_by(
    model: type[Base], expressions: Iterable[ModelOrderExpression]
) -> list[Any]:
    order: list[Any] = []
    for expression in expressions:
        column = _resolve_column(model, expression.field)
        order.append(column.desc() if expression.direction == "desc" else column.asc())
    return order
