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
from bots_place.domain.entities.user import UserBaseModel
from bots_place.domain.queries import GetUserBySessionQuery
from bots_place.infrastructure.mediator import Mediator
from bots_place.infrastructure.queries import GetUserBySessionHandler


@pytest.fixture
def mediator(uow: MagicMock) -> Mediator:
    mediator = Mediator()
    mediator.register(GetUserBySessionQuery, GetUserBySessionHandler(uow))
    return mediator


@pytest.fixture
async def container(mediator: Mediator) -> AsyncGenerator[AsyncContainer]:
    provider = Provider(scope=Scope.APP)
    provider.from_context(provides=Mediator, scope=Scope.APP)
    container = make_async_container(provider, context={Mediator: mediator})
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


async def test_user_api_with_unknown_session_returns_unauthorized(
    client: httpx.AsyncClient,
    uow: MagicMock,
) -> None:
    uow.sessions.get.return_value = None

    response = await client.get(
        UserPathEnum.API_USER,
        headers={"Cookie": f"{ACCESS_COOKIE}=unknown"},
    )

    assert response.status_code == 401


async def test_user_api_with_session_of_missing_user_returns_unauthorized(
    client: httpx.AsyncClient,
    uow: MagicMock,
    make_session: Callable[[int], str],
) -> None:
    uow.users.get.return_value = None
    token = make_session(7)

    response = await client.get(
        UserPathEnum.API_USER,
        headers={"Cookie": f"{ACCESS_COOKIE}={token}"},
    )

    assert response.status_code == 401


async def test_user_api_returns_profile_data(
    client: httpx.AsyncClient,
    uow: MagicMock,
    make_session: Callable[[int], str],
    make_user: Callable[..., UserBaseModel],
) -> None:
    user = make_user(id=7, email="menu@example.com")
    uow.users.get.return_value = user
    token = make_session(7)

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
