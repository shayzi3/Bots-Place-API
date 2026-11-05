from fastapi import FastAPI
from starlette.requests import Request

from bots_place.app.controllers.rest.routers.auth.depends.read_confirmation import (
    ReadConfirmation,
)
from bots_place.app.security.tokens import ConfirmationPurpose, TokenService
from bots_place.config.env import JwtSettings


class FakeContainer:
    def __init__(self, tokens: TokenService) -> None:
        self._tokens = tokens

    async def get(self, _type: object) -> TokenService:
        return self._tokens


def make_service(*, pending_ttl_minutes: int = 15) -> TokenService:
    return TokenService(
        JwtSettings(
            secret="x" * 32,
            algorithm="HS256",
            access_ttl_minutes=60,
            pending_ttl_minutes=pending_ttl_minutes,
        )
    )


def make_request(tokens: TokenService, cookie: str | None = None) -> Request:
    headers = []
    if cookie is not None:
        headers.append((b"cookie", f"pending_token={cookie}".encode()))
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/auth/confirm",
        "headers": headers,
        "query_string": b"",
        "app": FastAPI(),
        "state": {"dishka_container": FakeContainer(tokens)},
    }
    return Request(scope)


async def test_no_cookie_returns_none() -> None:
    result = await ReadConfirmation()(make_request(make_service()))
    assert result is None


async def test_valid_cookie_returns_payload() -> None:
    service = make_service()
    token = service.create_confirmation("a@b.c", ConfirmationPurpose.REGISTER)
    result = await ReadConfirmation()(make_request(service, token))
    assert result is not None
    assert result.email == "a@b.c"
    assert result.purpose is ConfirmationPurpose.REGISTER


async def test_invalid_cookie_returns_none() -> None:
    result = await ReadConfirmation()(make_request(make_service(), "garbage"))
    assert result is None


async def test_expired_cookie_returns_none() -> None:
    service = make_service(pending_ttl_minutes=-1)
    token = service.create_confirmation("a@b.c", ConfirmationPurpose.LOGIN)
    result = await ReadConfirmation()(make_request(service, token))
    assert result is None


async def test_access_token_in_pending_cookie_returns_none() -> None:
    service = make_service()
    token = service.create_access(1, "a@b.c")
    result = await ReadConfirmation()(make_request(service, token))
    assert result is None


async def test_tampered_cookie_returns_none() -> None:
    service = make_service()
    token = service.create_confirmation("a@b.c", ConfirmationPurpose.LOGIN) + "x"
    result = await ReadConfirmation()(make_request(service, token))
    assert result is None
