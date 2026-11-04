from typing import Any, TypeVar

from bots_place.domain.exceptions.mediator import HandlerNotFoundError
from bots_place.infrastructure.commands.base import CommandHandler

C = TypeVar("C")
R = TypeVar("R")


class Mediator:
    """Maps commands to their handlers and dispatches them."""

    def __init__(self) -> None:
        self._handlers: dict[type[Any], CommandHandler[Any, Any]] = {}

    def register(
        self,
        command_type: type[C],
        handler: CommandHandler[C, R],
    ) -> None:
        self._handlers[command_type] = handler

    async def send(self, command: C) -> Any:
        handler = self._handlers.get(type(command))
        if handler is None:
            raise HandlerNotFoundError(type(command))
        return await handler.handle(command)
