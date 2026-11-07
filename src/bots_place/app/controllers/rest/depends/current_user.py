from typing import Annotated

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import Depends, Request

from bots_place.app.controllers.rest.routers.auth.utils.cookies import ACCESS_COOKIE
from bots_place.app.security.tokens import TokenService
from bots_place.domain.entities.user import UserBaseModel
from bots_place.domain.exceptions import InvalidTokenError
from bots_place.domain.queries import GetUserByIdQuery
from bots_place.infrastructure.mediator import Mediator


async def get_current_user(
    token: str | None,
    tokens: TokenService,
    mediator: Mediator,
) -> UserBaseModel | None:
    if token is None:
        return None
    try:
        payload = tokens.decode_access(token)
    except InvalidTokenError:
        return None
    return await mediator.send(GetUserByIdQuery(user_id=payload.user_id))


@inject
async def current_user(
    request: Request,
    tokens: FromDishka[TokenService],
    mediator: FromDishka[Mediator],
) -> UserBaseModel | None:
    return await get_current_user(
        request.cookies.get(ACCESS_COOKIE),
        tokens,
        mediator,
    )


CurrentUser = Annotated[UserBaseModel | None, Depends(current_user)]
