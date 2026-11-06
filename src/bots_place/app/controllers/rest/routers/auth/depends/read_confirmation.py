from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends, Request
from pydantic import ValidationError

from bots_place.app.controllers.rest.routers.auth.utils.cookies import (
    CONFIRMATION_SESSION,
    clear_request_session,
)
from bots_place.app.security.tokens import ConfirmationTokenPayload


class ReadConfirmation:
    """FastAPI dependency: reads the pending confirmation from the session.

    Returns ``None`` when the session has no confirmation. Malformed or expired
    confirmations are removed from the session and also return ``None``.
    """

    async def __call__(self, request: Request) -> ConfirmationTokenPayload | None:
        data = request.session.get(CONFIRMATION_SESSION)
        if data is None:
            return None
        try:
            payload = ConfirmationTokenPayload.model_validate(data)
        except ValidationError:
            clear_request_session(request)
            return None
        if payload.expires_at <= datetime.now(UTC):
            clear_request_session(request)
            return None
        return payload


Confirmation = Annotated[ConfirmationTokenPayload | None, Depends(ReadConfirmation())]
