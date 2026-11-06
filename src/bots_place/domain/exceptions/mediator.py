from .base import AppError


class MediatorError(AppError):
    """Base class for mediator failures."""


class HandlerNotFoundError(MediatorError):
    """Raised when the mediator has no handler registered for a command."""

    def __init__(self, command_type: type[object]) -> None:
        super().__init__(f"No handler registered for command {command_type.__name__}")
        self.command_type = command_type
