from typing import Protocol


class EmailSender(Protocol):
    async def send_code(self, email: str, code: str) -> None: ...
