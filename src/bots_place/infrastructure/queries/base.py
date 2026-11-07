from typing import Protocol

from pydantic import BaseModel


class QueryHandler[Q: BaseModel, R](Protocol):
    """Handler for a single query type, returning a result."""

    async def handle(self, query: Q) -> R: ...
