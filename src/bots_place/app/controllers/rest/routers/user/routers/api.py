from typing import Annotated

from dishka.integrations.fastapi import FromDishka
from fastapi import APIRouter, Form, Request
from fastapi.responses import JSONResponse, RedirectResponse

from bots_place.app.controllers.rest.depends import CurrentUser
from bots_place.app.controllers.rest.response import (
    BaseResponse,
    error,
    error_responses,
    ok,
)
from bots_place.app.controllers.rest.route import ApiExceptionRoute
from bots_place.app.controllers.rest.routers.auth.schema.retry import (
    RetryAfterSchema,
)
from bots_place.app.controllers.rest.routers.auth.utils.cookies import (
    set_request_session_confirmation,
)
from bots_place.app.controllers.rest.routers.user.schema import (
    ChangeUserEmailSchema,
    ChangeUsernameSchema,
    UserProfileSchema,
)
from bots_place.app.core.api_path import AuthPathEnum, RootPathEnum, UserPathEnum
from bots_place.app.core.doc.base_exception_msg import BaseExceptionMessageEnum
from bots_place.app.core.doc.status_code import StatusCodeEnum
from bots_place.app.core.doc.user import (
    UserExceptionMessageEnum,
    UserSuccessMessageEnum,
    UserSummaryEnum,
)
from bots_place.app.security.tokens import ConfirmationPurpose, TokenService
from bots_place.domain.commands import (
    ChangeUserEmailCommand,
    ChangeUsernameCommand,
    UseEmailChangeLinkCommand,
)
from bots_place.domain.exceptions import (
    EmailAlreadyExistsError,
    EmailChangeLinkInvalidError,
    ResendCooldownError,
    UserNotFoundError,
)
from bots_place.infrastructure.mediator import Mediator

user_api_router = APIRouter(route_class=ApiExceptionRoute)


@user_api_router.get(
    UserPathEnum.API_USER,
    summary=UserSummaryEnum.API_USER,
    tags=["User API"],
    responses={
        StatusCodeEnum.OK: {
            "model": BaseResponse[UserProfileSchema],
            "description": UserSuccessMessageEnum.PROFILE,
        },
        **error_responses(unauthorized=True, internal=True),
    },
)
async def get_user(user: CurrentUser) -> JSONResponse:
    if user is None:
        return error(
            StatusCodeEnum.UNAUTHORIZED,
            BaseExceptionMessageEnum.NOT_AUTHENTICATED,
        )
    return ok(
        UserProfileSchema(
            id=user.id,
            username=user.username,
            email=user.email,
            created_at=user.created_at,
        )
    )


@user_api_router.patch(
    UserPathEnum.API_CHANGE_USERNAME,
    summary=UserSummaryEnum.API_CHANGE_USERNAME,
    tags=["User API"],
    responses={
        StatusCodeEnum.OK: {
            "model": BaseResponse[UserProfileSchema],
            "description": UserSuccessMessageEnum.PROFILE,
        },
        **error_responses(unauthorized=True, validation=True, internal=True),
    },
)
async def change_username(
    schema: Annotated[ChangeUsernameSchema, Form()],
    user: CurrentUser,
    mediator: FromDishka[Mediator],
) -> JSONResponse:
    if user is None:
        return error(
            StatusCodeEnum.UNAUTHORIZED,
            BaseExceptionMessageEnum.NOT_AUTHENTICATED,
        )
    try:
        updated = await mediator.send(
            ChangeUsernameCommand(user_id=user.id, new_username=schema.username)
        )
    except UserNotFoundError:
        return error(
            StatusCodeEnum.UNAUTHORIZED,
            BaseExceptionMessageEnum.NOT_AUTHENTICATED,
        )
    return ok(
        UserProfileSchema(
            id=updated.id,
            username=updated.username,
            email=updated.email,
            created_at=updated.created_at,
        )
    )


@user_api_router.post(
    UserPathEnum.API_CHANGE_USER_EMAIL_LINK,
    summary=UserSummaryEnum.API_CHANGE_USER_EMAIL_LINK,
    tags=["User API"],
    responses={
        StatusCodeEnum.OK: {
            "model": BaseResponse,
            "description": UserSuccessMessageEnum.EMAIL_CHANGE_LINK_SENT,
        },
        StatusCodeEnum.CONFLICT: {
            "model": BaseResponse,
            "description": UserExceptionMessageEnum.EMAIL_ALREADY_EXISTS,
        },
        StatusCodeEnum.TOO_MANY_REQUESTS: {
            "model": BaseResponse[RetryAfterSchema],
            "description": UserExceptionMessageEnum.EMAIL_CHANGE_COOLDOWN,
        },
        **error_responses(unauthorized=True, validation=True, internal=True),
    },
)
async def change_user_email_link(
    schema: Annotated[ChangeUserEmailSchema, Form()],
    user: CurrentUser,
    mediator: FromDishka[Mediator],
    request: Request,
) -> JSONResponse:
    if user is None:
        return error(
            StatusCodeEnum.UNAUTHORIZED,
            BaseExceptionMessageEnum.NOT_AUTHENTICATED,
        )
    base_url = str(request.base_url).rstrip("/")
    try:
        await mediator.send(
            ChangeUserEmailCommand(
                user_id=user.id,
                new_email=schema.email,
                link_url=f"{base_url}{UserPathEnum.API_CHANGE_USER_EMAIL}",
            )
        )
    except UserNotFoundError:
        return error(
            StatusCodeEnum.UNAUTHORIZED,
            BaseExceptionMessageEnum.NOT_AUTHENTICATED,
        )
    except EmailAlreadyExistsError:
        return error(
            StatusCodeEnum.CONFLICT,
            UserExceptionMessageEnum.EMAIL_ALREADY_EXISTS,
        )
    except ResendCooldownError as exc:
        return error(
            StatusCodeEnum.TOO_MANY_REQUESTS,
            UserExceptionMessageEnum.EMAIL_CHANGE_COOLDOWN,
            RetryAfterSchema(retry_after=exc.retry_after),
        )
    return ok(msg=UserSuccessMessageEnum.EMAIL_CHANGE_LINK_SENT)


@user_api_router.get(
    UserPathEnum.API_CHANGE_USER_EMAIL,
    summary=UserSummaryEnum.API_CHANGE_USER_EMAIL,
    tags=["User API"],
    responses={
        StatusCodeEnum.SEE_OTHER: {
            "description": UserSuccessMessageEnum.EMAIL_CHANGE_LINK_VALID,
        },
        **error_responses(validation=True, internal=True),
    },
)
async def change_user_email(
    token: str,
    request: Request,
    mediator: FromDishka[Mediator],
    tokens: FromDishka[TokenService],
) -> RedirectResponse:
    try:
        change = await mediator.send(UseEmailChangeLinkCommand(token=token))
    except EmailChangeLinkInvalidError:
        return RedirectResponse(
            RootPathEnum.PAGE_ROOT,
            status_code=StatusCodeEnum.SEE_OTHER,
        )
    set_request_session_confirmation(
        request=request,
        email=change.new_email,
        purpose=ConfirmationPurpose.CHANGE_EMAIL,
        ttl_seconds=tokens.confirmation_ttl_seconds,
        payload={"user_id": change.user_id},
    )
    return RedirectResponse(
        AuthPathEnum.PAGE_CONFIRM,
        status_code=StatusCodeEnum.SEE_OTHER,
    )
