from typing import Annotated

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import Depends, Request

from bots_place.app.controllers.rest.routers.auth.utils.cookies import ACCESS_COOKIE
from bots_place.domain.entities.user import UserBaseModel
from bots_place.domain.queries import GetUserBySessionQuery
from bots_place.infrastructure.mediator import Mediator


async def get_current_user(
    token: str | None,
    mediator: Mediator,
) -> UserBaseModel | None:
    if token is None:
        return None
    return await mediator.send(GetUserBySessionQuery(token=token))


@inject
async def current_user(
    request: Request,
    mediator: FromDishka[Mediator],
) -> UserBaseModel | None:
    return await get_current_user(request.cookies.get(ACCESS_COOKIE), mediator)


CurrentUser = Annotated[UserBaseModel | None, Depends(current_user)]
