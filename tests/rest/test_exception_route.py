import httpx
import pytest
from fastapi import APIRouter, FastAPI, HTTPException

from bots_place.app.controllers.rest.route import (
    ApiExceptionRoute,
    TemplateExceptionRoute,
)
from bots_place.app.core.doc.base_exception_msg import BaseExceptionMessageEnum
from bots_place.domain.exceptions import AppError


def make_app() -> FastAPI:
    api = APIRouter(route_class=ApiExceptionRoute)
    template = APIRouter(route_class=TemplateExceptionRoute)

    @api.get("/api/boom")
    async def api_boom() -> None:
        raise RuntimeError("secret detail")

    @api.get("/api/missing")
    async def api_missing() -> None:
        raise HTTPException(status_code=404, detail="nope")

    @api.get("/api/domain")
    async def api_domain() -> None:
        raise AppError("domain failure")

    @template.get("/page/boom")
    async def page_boom() -> None:
        raise RuntimeError("secret detail")

    app = FastAPI()
    app.include_router(api)
    app.include_router(template)
    return app


@pytest.fixture
async def client() -> httpx.AsyncClient:
    transport = httpx.ASGITransport(app=make_app(), raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="http://t") as c:
        yield c


async def test_api_unhandled_error_returns_json_500(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/boom")

    assert response.status_code == 500
    assert response.json() == {
        "status_code": 500,
        "msg": BaseExceptionMessageEnum.INTERNAL_ERROR,
        "data": None,
    }
    assert "secret detail" not in response.text


async def test_template_unhandled_error_returns_html_500(
    client: httpx.AsyncClient,
) -> None:
    response = await client.get("/page/boom")

    assert response.status_code == 500
    assert "text/html" in response.headers["content-type"]
    assert BaseExceptionMessageEnum.INTERNAL_ERROR in response.text
    assert "secret detail" not in response.text


async def test_http_exception_is_passed_through(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/missing")

    assert response.status_code == 404
    assert response.json() == {"detail": "nope"}


async def test_app_error_returns_json_500(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/domain")

    assert response.status_code == 500
    assert response.json()["msg"] == BaseExceptionMessageEnum.INTERNAL_ERROR
