from fastapi import FastAPI

from .auth.routers import api_router, template_router


def include_routers(app: FastAPI) -> None:
    app.include_router(template_router)
    app.include_router(api_router)
