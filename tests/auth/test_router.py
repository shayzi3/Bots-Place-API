import base64
import json
from collections.abc import AsyncGenerator, Callable
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
import pytest
from dishka import AsyncContainer, Provider, Scope, make_async_container
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI
from itsdangerous import TimestampSigner
from starlette.middleware.sessions import SessionMiddleware

from bots_place.app.controllers.rest.routers import include_routers
from bots_place.app.controllers.rest.routers.auth.utils.cookies import (
    ACCESS_COOKIE,
    CONFIRMATION_SESSION,
)
from bots_place.app.core.doc.auth.exception_msg import AuthExceptionMessageEnum
from bots_place.app.core.doc.status_code import StatusCodeEnum
from bots_place.app.security.tokens import ConfirmationPurpose, TokenService
from bots_place.config.env import CodeSettings, CookieSettings, JwtSettings
from bots_place.domain.commands import (
    ConfirmLoginCommand,
    ConfirmRegistrationCommand,
    RegisterUserCommand,
    RequestLoginCodeCommand,
    ResendCodeCommand,
)
from bots_place.domain.entities.email_code import EmailCodePurposeEnum
from bots_place.domain.exceptions.user import (
    EmailAlreadyExistsError,
    InvalidEmailCodeError,
    LoginNotAllowedError,
    ResendCooldownError,
    ResendNotAllowedError,
)
from bots_place.infrastructure.mediator import Mediator

SESSION_SECRET = "test-session-secret"
SESSION_COOKIE = "session"


class FakeMediator:
    def __init__(self) -> None:
        self.commands: list[Any] = []
        self.result: Any = None
        self.error: Exception | None = None

    async def send(self, command: Any) -> Any:
        self.commands.append(command)
        if self.error is not None:
            raise self.error
        return self.result


@pytest.fixture
def mediator() -> FakeMediator:
    return FakeMediator()


@pytest.fixture
def tokens(jwt_settings: JwtSettings) -> TokenService:
    return TokenService(jwt_settings)


@pytest.fixture
async def container(
    mediator: FakeMediator, tokens: TokenService
) -> AsyncGenerator[AsyncContainer]:
    provider = Provider(scope=Scope.APP)
    provider.from_context(provides=Mediator, scope=Scope.APP)
    provider.from_context(provides=TokenService, scope=Scope.APP)
    provider.from_context(provides=CookieSettings, scope=Scope.APP)
    provider.from_context(provides=CodeSettings, scope=Scope.APP)
    container = make_async_container(
        provider,
        context={
            Mediator: mediator,
            TokenService: tokens,
            CookieSettings: CookieSettings(secure=False, samesite="lax"),
            CodeSettings: CodeSettings(resend_cooldown_seconds=60),
        },
    )
    yield container
    await container.close()


@pytest.fixture
async def client(container: AsyncContainer) -> AsyncGenerator[httpx.AsyncClient]:
    app = FastAPI()
    app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET)
    include_routers(app)
    setup_dishka(container, app)
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://test"
    ) as http_client:
        yield http_client


@pytest.fixture
def set_cookies() -> Callable[[httpx.Response], list[str]]:
    def _get(response: httpx.Response) -> list[str]:
        return response.headers.get_list("set-cookie")

    return _get


def _session_headers(
    email: str = "user@example.com",
    purpose: ConfirmationPurpose = ConfirmationPurpose.LOGIN,
    *,
    expires_in: int = 900,
) -> dict[str, str]:
    expires_at = datetime.now(UTC) + timedelta(seconds=expires_in)
    data = {
        CONFIRMATION_SESSION: {
            "email": email,
            "purpose": purpose.value,
            "expires_at": expires_at.isoformat(),
        }
    }
    raw = base64.b64encode(json.dumps(data).encode("utf-8"))
    value = TimestampSigner(SESSION_SECRET).sign(raw).decode("utf-8")
    return {"cookie": f"{SESSION_COOKIE}={value}"}


def _session_data(headers: list[str]) -> dict[str, Any]:
    value = _cookie_value(headers, SESSION_COOKIE).strip('"')
    raw = TimestampSigner(SESSION_SECRET).unsign(value)
    data: dict[str, Any] = json.loads(base64.b64decode(raw))
    return data[CONFIRMATION_SESSION]


def _cookie_header(headers: list[str], name: str) -> str | None:
    for header in headers:
        if header.startswith(f"{name}="):
            return header
    return None


def _cookie_value(headers: list[str], name: str) -> str:
    header = _cookie_header(headers, name)
    assert header is not None
    return header.split(";", 1)[0].split("=", 1)[1]


async def test_login_page_renders_google_error_from_query(
    client: httpx.AsyncClient,
) -> None:
    response = await client.get("/auth/login", params={"error": "google"})

    assert response.status_code == 200
    assert "Не удалось войти через Google" in response.text


async def test_register_page_renders(client: httpx.AsyncClient) -> None:
    response = await client.get("/auth/register")

    assert response.status_code == 200
    assert 'name="email"' in response.text


async def test_register_new_user_stores_confirmation_in_session(
    client: httpx.AsyncClient,
    mediator: FakeMediator,
    set_cookies: Callable[[httpx.Response], list[str]],
) -> None:
    response = await client.post(
        "/api/v1/auth/register",
        data={"email": "new@example.com", "username": "new"},
    )

    assert response.status_code == StatusCodeEnum.OK
    assert response.json()["status_code"] == StatusCodeEnum.OK
    assert mediator.commands == [
        RegisterUserCommand(email="new@example.com", username="new")
    ]
    assert response.json()["data"] == {"retry_after": 60}

    data = _session_data(set_cookies(response))
    assert data["email"] == "new@example.com"
    assert data["purpose"] == ConfirmationPurpose.REGISTER.value
    assert "expires_at" in data


async def test_register_existing_verified_user_returns_conflict(
    client: httpx.AsyncClient,
    mediator: FakeMediator,
    set_cookies: Callable[[httpx.Response], list[str]],
) -> None:
    mediator.error = EmailAlreadyExistsError("user@example.com")

    response = await client.post(
        "/api/v1/auth/register",
        data={"email": "user@example.com", "username": "user"},
    )

    assert response.status_code == StatusCodeEnum.CONFLICT
    body = response.json()
    assert body["status_code"] == StatusCodeEnum.CONFLICT
    assert body["msg"] == AuthExceptionMessageEnum.EMAIL_ALREADY_EXISTS
    assert _cookie_header(set_cookies(response), SESSION_COOKIE) is None


async def test_login_known_user_stores_login_confirmation_in_session(
    client: httpx.AsyncClient,
    mediator: FakeMediator,
    set_cookies: Callable[[httpx.Response], list[str]],
) -> None:
    response = await client.post(
        "/api/v1/auth/login", data={"email": "user@example.com"}
    )

    assert response.status_code == StatusCodeEnum.OK
    assert mediator.commands == [RequestLoginCodeCommand(email="user@example.com")]
    assert response.json()["data"] == {"retry_after": 60}

    data = _session_data(set_cookies(response))
    assert data["purpose"] == ConfirmationPurpose.LOGIN.value


async def test_login_unknown_user_returns_forbidden(
    client: httpx.AsyncClient,
    mediator: FakeMediator,
    set_cookies: Callable[[httpx.Response], list[str]],
) -> None:
    mediator.error = LoginNotAllowedError("ghost@example.com")

    response = await client.post(
        "/api/v1/auth/login", data={"email": "ghost@example.com"}
    )

    assert response.status_code == StatusCodeEnum.FORBIDDEN
    assert response.json()["msg"] == AuthExceptionMessageEnum.LOGIN_NOT_ALLOWED
    assert _cookie_header(set_cookies(response), SESSION_COOKIE) is None


async def test_confirm_page_without_session_redirects_to_login(
    client: httpx.AsyncClient,
) -> None:
    response = await client.get("/auth/confirm")

    assert response.status_code == StatusCodeEnum.SEE_OTHER
    assert response.headers["location"] == "/auth/login"


async def test_confirm_page_with_session_renders_form(
    client: httpx.AsyncClient,
) -> None:
    response = await client.get("/auth/confirm", headers=_session_headers())

    assert response.status_code == 200
    assert 'name="code"' in response.text


async def test_confirm_page_with_expired_session_redirects_to_login(
    client: httpx.AsyncClient,
) -> None:
    response = await client.get(
        "/auth/confirm", headers=_session_headers(expires_in=-1)
    )

    assert response.status_code == StatusCodeEnum.SEE_OTHER
    assert response.headers["location"] == "/auth/login"


async def test_confirm_post_without_session_returns_unauthorized(
    client: httpx.AsyncClient, mediator: FakeMediator
) -> None:
    response = await client.post("/api/v1/auth/confirm", data={"code": "123456"})

    assert response.status_code == StatusCodeEnum.UNAUTHORIZED
    assert response.json()["msg"] == AuthExceptionMessageEnum.INVALID_PENDING_TOKEN
    assert mediator.commands == []


async def test_confirm_registration_sets_access_cookie_and_clears_session(
    client: httpx.AsyncClient,
    mediator: FakeMediator,
    tokens: TokenService,
    make_user: Callable[..., Any],
    set_cookies: Callable[[httpx.Response], list[str]],
) -> None:
    mediator.result = make_user(id=7, email="user@example.com", is_verified=True)

    response = await client.post(
        "/api/v1/auth/confirm",
        data={"code": "123456"},
        headers=_session_headers("user@example.com", ConfirmationPurpose.REGISTER),
    )

    assert response.status_code == StatusCodeEnum.OK
    assert mediator.commands == [
        ConfirmRegistrationCommand(email="user@example.com", code="123456")
    ]

    headers = set_cookies(response)
    payload = tokens.decode_access(_cookie_value(headers, ACCESS_COOKIE))
    assert payload.user_id == 7
    assert payload.email == "user@example.com"

    session = _cookie_header(headers, SESSION_COOKIE)
    assert session is not None
    assert "1970" in session


async def test_confirm_login_dispatches_login_command(
    client: httpx.AsyncClient,
    mediator: FakeMediator,
    make_user: Callable[..., Any],
    set_cookies: Callable[[httpx.Response], list[str]],
) -> None:
    mediator.result = make_user(id=3, email="user@example.com", is_verified=True)

    response = await client.post(
        "/api/v1/auth/confirm",
        data={"code": "654321"},
        headers=_session_headers("user@example.com", ConfirmationPurpose.LOGIN),
    )

    assert response.status_code == StatusCodeEnum.OK
    assert mediator.commands == [
        ConfirmLoginCommand(email="user@example.com", code="654321")
    ]
    assert _cookie_header(set_cookies(response), ACCESS_COOKIE) is not None


async def test_confirm_invalid_code_returns_bad_request(
    client: httpx.AsyncClient,
    mediator: FakeMediator,
    set_cookies: Callable[[httpx.Response], list[str]],
) -> None:
    mediator.error = InvalidEmailCodeError()

    response = await client.post(
        "/api/v1/auth/confirm",
        data={"code": "000000"},
        headers=_session_headers("user@example.com", ConfirmationPurpose.REGISTER),
    )

    assert response.status_code == StatusCodeEnum.BAD_REQUEST
    assert response.json()["msg"] == AuthExceptionMessageEnum.INVALID_EMAIL_CODE
    assert _cookie_header(set_cookies(response), ACCESS_COOKIE) is None


async def test_logout_clears_access_cookie_and_session(
    client: httpx.AsyncClient,
    set_cookies: Callable[[httpx.Response], list[str]],
) -> None:
    response = await client.post("/api/v1/auth/logout", headers=_session_headers())

    assert response.status_code == StatusCodeEnum.OK

    headers = set_cookies(response)
    access = _cookie_header(headers, ACCESS_COOKIE)
    session = _cookie_header(headers, SESSION_COOKIE)
    assert access is not None
    assert "Max-Age=0" in access
    assert session is not None
    assert "1970" in session


async def test_confirm_page_renders_resend_button(
    client: httpx.AsyncClient,
) -> None:
    response = await client.get("/auth/confirm", headers=_session_headers())

    assert response.status_code == 200
    assert 'action="/api/v1/auth/resend"' in response.text
    assert 'id="resend-btn"' in response.text
    assert "data-seconds" not in response.text


async def test_resend_without_session_returns_unauthorized(
    client: httpx.AsyncClient, mediator: FakeMediator
) -> None:
    response = await client.post("/api/v1/auth/resend")

    assert response.status_code == StatusCodeEnum.UNAUTHORIZED
    assert response.json()["msg"] == AuthExceptionMessageEnum.INVALID_PENDING_TOKEN
    assert mediator.commands == []


async def test_resend_registration_returns_ok_and_extends_session(
    client: httpx.AsyncClient,
    mediator: FakeMediator,
    set_cookies: Callable[[httpx.Response], list[str]],
) -> None:
    response = await client.post(
        "/api/v1/auth/resend",
        headers=_session_headers("user@example.com", ConfirmationPurpose.REGISTER),
    )

    assert response.status_code == StatusCodeEnum.OK
    assert response.json()["data"] == {"retry_after": 60}
    data = _session_data(set_cookies(response))
    assert data["email"] == "user@example.com"
    assert data["purpose"] == ConfirmationPurpose.REGISTER.value
    assert mediator.commands == [
        ResendCodeCommand(
            email="user@example.com", purpose=EmailCodePurposeEnum.REGISTRATION
        )
    ]


async def test_resend_login_dispatches_login_purpose(
    client: httpx.AsyncClient, mediator: FakeMediator
) -> None:
    await client.post(
        "/api/v1/auth/resend",
        headers=_session_headers("user@example.com", ConfirmationPurpose.LOGIN),
    )

    assert mediator.commands == [
        ResendCodeCommand(email="user@example.com", purpose=EmailCodePurposeEnum.LOGIN)
    ]


async def test_resend_during_cooldown_returns_too_many_requests(
    client: httpx.AsyncClient, mediator: FakeMediator
) -> None:
    mediator.error = ResendCooldownError(retry_after=33)

    response = await client.post("/api/v1/auth/resend", headers=_session_headers())

    assert response.status_code == StatusCodeEnum.TOO_MANY_REQUESTS
    body = response.json()
    assert body["msg"] == AuthExceptionMessageEnum.RESEND_COOLDOWN
    assert body["data"] == {"retry_after": 33}


async def test_resend_not_allowed_returns_forbidden(
    client: httpx.AsyncClient, mediator: FakeMediator
) -> None:
    mediator.error = ResendNotAllowedError("user@example.com")

    response = await client.post("/api/v1/auth/resend", headers=_session_headers())

    assert response.status_code == StatusCodeEnum.FORBIDDEN
    assert response.json()["msg"] == AuthExceptionMessageEnum.RESEND_NOT_ALLOWED
