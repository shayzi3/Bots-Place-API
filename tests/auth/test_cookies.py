from fastapi import Response

from bots_place.app.controllers.rest.routers.auth.utils.cookies import (
    ACCESS_COOKIE,
    clear_auth_cookie,
    set_auth_cookie,
)
from bots_place.config.env import CookieSettings


def _set_cookie_header(response: Response, name: str) -> str:
    for header in response.headers.getlist("set-cookie"):
        if header.startswith(f"{name}="):
            return header
    raise AssertionError(f"cookie {name} was not set")


def test_set_auth_cookie_sets_security_attributes() -> None:
    response = Response()
    settings = CookieSettings(secure=True, samesite="strict", domain="example.com")

    set_auth_cookie(response, ACCESS_COOKIE, "token-value", 3600, settings)

    header = _set_cookie_header(response, ACCESS_COOKIE)
    assert "access_token=token-value" in header
    assert "Max-Age=3600" in header
    assert "HttpOnly" in header
    assert "Secure" in header
    assert "SameSite=strict" in header
    assert "Domain=example.com" in header
    assert "Path=/" in header


def test_set_auth_cookie_without_secure_flags() -> None:
    response = Response()
    settings = CookieSettings(secure=False, samesite="lax")

    set_auth_cookie(response, ACCESS_COOKIE, "pending", 900, settings)

    header = _set_cookie_header(response, ACCESS_COOKIE)
    assert "HttpOnly" in header
    assert "Secure" not in header
    assert "SameSite=lax" in header
    assert "Domain=" not in header


def test_clear_auth_cookie_expires_cookie() -> None:
    response = Response()

    clear_auth_cookie(response, ACCESS_COOKIE, CookieSettings())

    header = _set_cookie_header(response, ACCESS_COOKIE)
    assert header.startswith(f"{ACCESS_COOKIE}=")
    assert "Max-Age=0" in header
    assert "Path=/" in header
