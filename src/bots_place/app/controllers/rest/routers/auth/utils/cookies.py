from fastapi import Response

from bots_place.config.env import CookieSettings

ACCESS_COOKIE = "access_token"
PENDING_COOKIE = "pending_token"


def set_auth_cookie(
    response: Response,
    name: str,
    value: str,
    max_age: int,
    settings: CookieSettings,
) -> None:
    response.set_cookie(
        key=name,
        value=value,
        max_age=max_age,
        httponly=True,
        secure=settings.secure,
        samesite=settings.samesite,
        domain=settings.domain,
        path="/",
    )


def clear_auth_cookie(
    response: Response,
    name: str,
    settings: CookieSettings,
) -> None:
    response.delete_cookie(
        key=name,
        domain=settings.domain,
        path="/",
    )
