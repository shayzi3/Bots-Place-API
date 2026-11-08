from typing import Protocol


class EmailSender(Protocol):
    async def send_code(self, email: str, code: str) -> None: ...

    async def send_link(self, email: str, link: str) -> None: ...
