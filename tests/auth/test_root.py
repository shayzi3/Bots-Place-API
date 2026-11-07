from collections.abc import AsyncGenerator, Callable
from unittest.mock import MagicMock

import httpx
import pytest
from dishka import AsyncContainer, Provider, Scope, make_async_container
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI

from bots_place.app.controllers.rest.routers import include_routers
from bots_place.app.controllers.rest.routers.auth.utils.cookies import ACCESS_COOKIE
from bots_place.app.security.tokens import TokenService
from bots_place.config.env import JwtSettings
from bots_place.domain.entities.user import UserBaseModel
from bots_place.domain.queries import GetUserByIdQuery
from bots_place.infrastructure.mediator import Mediator
from bots_place.infrastructure.queries import GetUserByIdHandler


@pytest.fixture
def tokens(jwt_settings: JwtSettings) -> TokenService:
    return TokenService(jwt_settings)


@pytest.fixture
def mediator(uow: MagicMock) -> Mediator:
    mediator = Mediator()
    mediator.register(GetUserByIdQuery, GetUserByIdHandler(uow))
    return mediator


@pytest.fixture
async def container(
    mediator: Mediator, tokens: TokenService
) -> AsyncGenerator[AsyncContainer]:
    provider = Provider(scope=Scope.APP)
    provider.from_context(provides=TokenService, scope=Scope.APP)
    provider.from_context(provides=Mediator, scope=Scope.APP)
    container = make_async_container(
        provider,
        context={TokenService: tokens, Mediator: mediator},
    )
    yield container
    await container.close()


@pytest.fixture
async def client(container: AsyncContainer) -> AsyncGenerator[httpx.AsyncClient]:
    app = FastAPI()
    include_routers(app)
    setup_dishka(container, app)
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://test"
    ) as http_client:
        yield http_client


async def test_get_user_by_id_handler_reads_user_from_repository(
    uow: MagicMock,
    make_user: Callable[..., UserBaseModel],
) -> None:
    expected = make_user(id=7)
    uow.users.get.return_value = expected
    handler = GetUserByIdHandler(uow)

    result = await handler.handle(GetUserByIdQuery(user_id=7))

    assert result == expected
    uow.users.get.assert_awaited_once()


async def test_root_without_cookie_shows_login_button(
    client: httpx.AsyncClient, uow: MagicMock
) -> None:
    response = await client.get("/")

    assert response.status_code == 200
    assert 'href="/auth/login"' in response.text
    assert "Профиль" not in response.text
    uow.users.get.assert_not_called()


async def test_root_with_valid_token_of_existing_user_shows_profile(
    client: httpx.AsyncClient,
    uow: MagicMock,
    tokens: TokenService,
    make_user: Callable[..., UserBaseModel],
) -> None:
    uow.users.get.return_value = make_user(id=7)
    token = tokens.create_access(user_id=7, email="user@example.com")

    response = await client.get("/", headers={"Cookie": f"{ACCESS_COOKIE}={token}"})

    assert response.status_code == 200
    assert "Профиль" in response.text
    assert 'href="/auth/login"' not in response.text


async def test_root_with_token_of_missing_user_shows_login_button(
    client: httpx.AsyncClient,
    uow: MagicMock,
    tokens: TokenService,
) -> None:
    uow.users.get.return_value = None
    token = tokens.create_access(user_id=7, email="user@example.com")

    response = await client.get("/", headers={"Cookie": f"{ACCESS_COOKIE}={token}"})

    assert response.status_code == 200
    assert 'href="/auth/login"' in response.text
    assert "Профиль" not in response.text


async def test_root_with_invalid_token_shows_login_button(
    client: httpx.AsyncClient, uow: MagicMock
) -> None:
    response = await client.get("/", headers={"Cookie": f"{ACCESS_COOKIE}=not-a-jwt"})

    assert response.status_code == 200
    assert 'href="/auth/login"' in response.text
    assert "Профиль" not in response.text
    uow.users.get.assert_not_called()
