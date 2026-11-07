from typing import Protocol

from pydantic import BaseModel


class CommandHandler[C: BaseModel, R](Protocol):
    """Handler for a single command type, returning a result."""

    async def handle(self, command: C) -> R: ...
