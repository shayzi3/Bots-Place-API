from fastapi import FastAPI

from .auth.routers import auth_api_router, auth_template_router
from .root.routers import root_template_router
from .user.routers import user_api_router


def include_routers(app: FastAPI) -> None:
    app.include_router(root_template_router)
    app.include_router(user_api_router)
    app.include_router(auth_template_router)
    app.include_router(auth_api_router)
