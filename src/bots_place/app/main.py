from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from dishka import AsyncContainer
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from bots_place.app.controllers.rest.middlewares.session import (
    setup_session_middleware,
)
from bots_place.app.controllers.rest.routers import include_routers
from bots_place.infrastructure.setup.cotainer import create_container, init_database

container: AsyncContainer = create_container()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    await init_database(container)

    try:
        yield
    finally:
        await container.close()


app = FastAPI(title="Bots Place", lifespan=lifespan)

setup_session_middleware(app)

include_routers(app)

app.mount(
    "/static",
    StaticFiles(directory=Path(__file__).parent / "controllers" / "rest" / "static"),
    name="static",
)

setup_dishka(container, app)


def main() -> None:
    uvicorn.run("bots_place.app.main:app", port=8086)


if __name__ == "__main__":
    main()
