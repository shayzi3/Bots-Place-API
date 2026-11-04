from typing import Protocol, TypeVar

C_contra = TypeVar("C_contra", contravariant=True)
R_co = TypeVar("R_co", covariant=True)


class CommandHandler(Protocol[C_contra, R_co]):
    """Handler for a single command type, returning a result."""

    async def handle(self, command: C_contra) -> R_co: ...
