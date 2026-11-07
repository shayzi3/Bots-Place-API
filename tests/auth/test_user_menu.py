from collections.abc import AsyncGenerator, Callable
from datetime import datetime
from unittest.mock import MagicMock

import httpx
import pytest
from dishka import AsyncContainer, Provider, Scope, make_async_container
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI

from bots_place.app.controllers.rest.routers import include_routers
from bots_place.app.controllers.rest.routers.auth.utils.cookies import ACCESS_COOKIE
from bots_place.app.core.api_path import UserPathEnum
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


async def test_user_api_without_cookie_returns_unauthorized(
    client: httpx.AsyncClient, uow: MagicMock
) -> None:
    response = await client.get(UserPathEnum.API_USER)

    assert response.status_code == 401
    assert response.json()["status_code"] == 401
    uow.users.get.assert_not_called()


async def test_user_api_with_invalid_token_returns_unauthorized(
    client: httpx.AsyncClient,
) -> None:
    response = await client.get(
        UserPathEnum.API_USER,
        headers={"Cookie": f"{ACCESS_COOKIE}=not-a-jwt"},
    )

    assert response.status_code == 401


async def test_user_api_with_token_of_missing_user_returns_unauthorized(
    client: httpx.AsyncClient,
    uow: MagicMock,
    tokens: TokenService,
) -> None:
    uow.users.get.return_value = None
    token = tokens.create_access(user_id=7, email="user@example.com")

    response = await client.get(
        UserPathEnum.API_USER,
        headers={"Cookie": f"{ACCESS_COOKIE}={token}"},
    )

    assert response.status_code == 401


async def test_user_api_returns_profile_data(
    client: httpx.AsyncClient,
    uow: MagicMock,
    tokens: TokenService,
    make_user: Callable[..., UserBaseModel],
) -> None:
    user = make_user(id=7, email="menu@example.com")
    uow.users.get.return_value = user
    token = tokens.create_access(user_id=7, email="menu@example.com")

    response = await client.get(
        UserPathEnum.API_USER,
        headers={"Cookie": f"{ACCESS_COOKIE}={token}"},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["id"] == 7
    assert data["username"] == user.username
    assert data["email"] == "menu@example.com"
    assert datetime.fromisoformat(data["created_at"]) == user.created_at
    assert "auth_from" not in data
    assert "is_verified" not in data
