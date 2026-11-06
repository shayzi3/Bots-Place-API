from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

from bots_place.config.env import settings


def setup_session_middleware(app: FastAPI) -> None:
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.session.secret_key,
        same_site="lax",
        https_only=settings.cookie.secure,
    )
