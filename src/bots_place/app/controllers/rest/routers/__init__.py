from fastapi import FastAPI

from .auth.router import auth_router


def include_routers(app: FastAPI) -> None:
    app.include_router(auth_router)
