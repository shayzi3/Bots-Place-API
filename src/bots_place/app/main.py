from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import uvicorn
from dishka import AsyncContainer
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI

from bots_place.app.controllers.rest.exceptions import register_exception_handlers
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

include_routers(app)

register_exception_handlers(app)

setup_dishka(container, app)


def main() -> None:
    uvicorn.run("bots_place.app.main:app", port=8086)


if __name__ == "__main__":
    main()
