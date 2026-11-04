from typing import Annotated

from dishka import AsyncContainer
from fastapi import Depends, Request

from bots_place.app.controllers.rest.routers.auth.utils.cookies import PENDING_COOKIE
from bots_place.app.security.tokens import ConfirmationTokenPayload, TokenService
from bots_place.domain.exceptions.user import InvalidTokenError


class ReadConfirmation:
    """FastAPI dependency: decodes the confirmation token from the cookie.

    Returns ``None`` when the cookie is missing or the token is invalid/expired.
    """

    async def __call__(self, request: Request) -> ConfirmationTokenPayload | None:
        container: AsyncContainer = request.state.dishka_container
        tokens = await container.get(TokenService)

        token = request.cookies.get(PENDING_COOKIE)
        if not token:
            return None
        try:
            return tokens.decode_confirmation(token)
        except InvalidTokenError:
            return None


Confirmation = Annotated[ConfirmationTokenPayload | None, Depends(ReadConfirmation())]
