from abc import ABC, abstractmethod
from dataclasses import dataclass

from starlette.requests import Request
from starlette.responses import Response


@dataclass(frozen=True)
class GoogleUserInfo:
    email: str
    name: str
    email_verified: bool


class GoogleAuth(ABC):
    @abstractmethod
    async def authorize_redirect(self, request: Request) -> Response: ...

    @abstractmethod
    async def fetch_user(self, request: Request) -> GoogleUserInfo: ...
