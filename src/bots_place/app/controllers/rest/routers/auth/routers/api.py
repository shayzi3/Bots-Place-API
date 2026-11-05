from typing import Annotated, Any

from dishka.integrations.fastapi import FromDishka
from fastapi import APIRouter, Form
from fastapi.responses import JSONResponse

from bots_place.app.controllers.rest.response import BaseResponse, error, ok
from bots_place.app.controllers.rest.route import ApiExceptionRoute
from bots_place.app.controllers.rest.routers.auth.depends import Confirmation
from bots_place.app.controllers.rest.routers.auth.schema.confirm import (
    ConfirmCodeForm,
)
from bots_place.app.controllers.rest.routers.auth.schema.retry import (
    RetryAfterSchema,
)
from bots_place.app.controllers.rest.routers.auth.utils.cookies import (
    ACCESS_COOKIE,
    PENDING_COOKIE,
    clear_auth_cookie,
    set_auth_cookie,
)
from bots_place.app.core.api_path import AuthPathEnum
from bots_place.app.core.doc.auth import AuthSummaryEnum
from bots_place.app.core.doc.auth.exception_msg import AuthExceptionMessageEnum
from bots_place.app.core.doc.auth.success_msg import AuthSuccessMessageEnum
from bots_place.app.core.doc.base_exception_msg import BaseExceptionMessageEnum
from bots_place.app.core.doc.status_code import StatusCodeEnum
from bots_place.app.security.tokens import ConfirmationPurpose, TokenService
from bots_place.config.env import CodeSettings, CookieSettings
from bots_place.domain.commands import (
    ConfirmLoginCommand,
    ConfirmRegistrationCommand,
    RegisterUserCommand,
    RequestLoginCodeCommand,
    ResendCodeCommand,
)
from bots_place.domain.entities.email_code import EmailCodePurposeEnum
from bots_place.domain.exceptions.user import (
    EmailAlreadyExistsError,
    InvalidEmailCodeError,
    LoginNotAllowedError,
    ResendCooldownError,
    ResendNotAllowedError,
)
from bots_place.infrastructure.mediator import Mediator

api_router = APIRouter(route_class=ApiExceptionRoute)

INTERNAL_RESPONSE: dict[int | str, dict[str, Any]] = {
    StatusCodeEnum.INTERNAL_SERVER_ERROR: {
        "model": BaseResponse,
        "description": BaseExceptionMessageEnum.INTERNAL_ERROR,
    },
}

VALIDATION_RESPONSE: dict[int | str, dict[str, Any]] = {
    StatusCodeEnum.UNPROCESSABLE_ENTITY: {
        "model": BaseResponse,
        "description": BaseExceptionMessageEnum.VALIDATION_ERROR,
    },
}


@api_router.post(
    AuthPathEnum.API_REGISTER,
    summary=AuthSummaryEnum.API_REGISTER,
    tags=["Auth API"],
    responses={
        StatusCodeEnum.OK: {
            "model": BaseResponse,
            "description": AuthSuccessMessageEnum.REGISTER_CODE_SENT,
        },
        **VALIDATION_RESPONSE,
        **INTERNAL_RESPONSE,
        StatusCodeEnum.CONFLICT: {
            "model": BaseResponse,
            "description": AuthExceptionMessageEnum.EMAIL_ALREADY_EXISTS,
        },
    },
)
async def register_user(
    command: Annotated[RegisterUserCommand, Form()],
    mediator: FromDishka[Mediator],
    tokens: FromDishka[TokenService],
    cookies: FromDishka[CookieSettings],
) -> JSONResponse:
    try:
        await mediator.send(command)
    except EmailAlreadyExistsError:
        return error(
            StatusCodeEnum.CONFLICT,
            AuthExceptionMessageEnum.EMAIL_ALREADY_EXISTS,
        )

    confirmation = tokens.create_confirmation(
        command.email, ConfirmationPurpose.REGISTER
    )
    response = ok()
    set_auth_cookie(
        response,
        PENDING_COOKIE,
        confirmation,
        tokens.confirmation_ttl_seconds,
        cookies,
    )
    return response


@api_router.post(
    AuthPathEnum.API_LOGIN,
    summary=AuthSummaryEnum.API_LOGIN,
    tags=["Auth API"],
    responses={
        StatusCodeEnum.OK: {
            "model": BaseResponse,
            "description": AuthSuccessMessageEnum.LOGIN_CODE_SENT,
        },
        **VALIDATION_RESPONSE,
        **INTERNAL_RESPONSE,
        StatusCodeEnum.FORBIDDEN: {
            "model": BaseResponse,
            "description": AuthExceptionMessageEnum.LOGIN_NOT_ALLOWED,
        },
    },
)
async def login_user(
    command: Annotated[RequestLoginCodeCommand, Form()],
    mediator: FromDishka[Mediator],
    tokens: FromDishka[TokenService],
    cookies: FromDishka[CookieSettings],
) -> JSONResponse:
    try:
        await mediator.send(command)
    except LoginNotAllowedError:
        return error(
            StatusCodeEnum.FORBIDDEN,
            AuthExceptionMessageEnum.LOGIN_NOT_ALLOWED,
        )

    confirmation = tokens.create_confirmation(command.email, ConfirmationPurpose.LOGIN)
    response = ok()
    set_auth_cookie(
        response,
        PENDING_COOKIE,
        confirmation,
        tokens.confirmation_ttl_seconds,
        cookies,
    )
    return response


@api_router.post(
    AuthPathEnum.API_CONFIRM,
    summary=AuthSummaryEnum.API_CONFIRM,
    tags=["Auth API"],
    responses={
        StatusCodeEnum.OK: {
            "model": BaseResponse,
            "description": AuthSuccessMessageEnum.CODE_CONFIRMED,
        },
        **VALIDATION_RESPONSE,
        **INTERNAL_RESPONSE,
        StatusCodeEnum.UNAUTHORIZED: {
            "model": BaseResponse,
            "description": AuthExceptionMessageEnum.INVALID_PENDING_TOKEN,
        },
        StatusCodeEnum.BAD_REQUEST: {
            "model": BaseResponse,
            "description": AuthExceptionMessageEnum.INVALID_EMAIL_CODE,
        },
    },
)
async def confirm(
    confirmation: Confirmation,
    form: Annotated[ConfirmCodeForm, Form()],
    mediator: FromDishka[Mediator],
    tokens: FromDishka[TokenService],
    cookies: FromDishka[CookieSettings],
) -> JSONResponse:
    if confirmation is None:
        return error(
            StatusCodeEnum.UNAUTHORIZED,
            AuthExceptionMessageEnum.INVALID_PENDING_TOKEN,
        )

    command: ConfirmRegistrationCommand | ConfirmLoginCommand
    if confirmation.purpose is ConfirmationPurpose.REGISTER:
        command = ConfirmRegistrationCommand(email=confirmation.email, code=form.code)
    elif confirmation.purpose is ConfirmationPurpose.LOGIN:
        command = ConfirmLoginCommand(email=confirmation.email, code=form.code)
    else:
        return error(
            StatusCodeEnum.UNAUTHORIZED,
            AuthExceptionMessageEnum.INVALID_PENDING_TOKEN,
        )

    try:
        user = await mediator.send(command)
    except InvalidEmailCodeError:
        return error(
            StatusCodeEnum.BAD_REQUEST,
            AuthExceptionMessageEnum.INVALID_EMAIL_CODE,
        )

    access = tokens.create_access(user.id, user.email)
    response = ok()
    clear_auth_cookie(response, PENDING_COOKIE, cookies)
    set_auth_cookie(response, ACCESS_COOKIE, access, tokens.access_ttl_seconds, cookies)
    return response


@api_router.post(
    AuthPathEnum.API_RESEND,
    summary=AuthSummaryEnum.API_RESEND,
    tags=["Auth API"],
    responses={
        StatusCodeEnum.OK: {
            "model": BaseResponse[RetryAfterSchema],
            "description": AuthSuccessMessageEnum.CODE_RESENT,
        },
        **INTERNAL_RESPONSE,
        StatusCodeEnum.UNAUTHORIZED: {
            "model": BaseResponse,
            "description": AuthExceptionMessageEnum.INVALID_PENDING_TOKEN,
        },
        StatusCodeEnum.FORBIDDEN: {
            "model": BaseResponse,
            "description": AuthExceptionMessageEnum.RESEND_NOT_ALLOWED,
        },
        StatusCodeEnum.TOO_MANY_REQUESTS: {
            "model": BaseResponse[RetryAfterSchema],
            "description": AuthExceptionMessageEnum.RESEND_COOLDOWN,
        },
    },
)
async def resend_code(
    confirmation: Confirmation,
    mediator: FromDishka[Mediator],
    code_settings: FromDishka[CodeSettings],
) -> JSONResponse:
    if confirmation is None:
        return error(
            StatusCodeEnum.UNAUTHORIZED,
            AuthExceptionMessageEnum.INVALID_PENDING_TOKEN,
        )

    if confirmation.purpose is ConfirmationPurpose.REGISTER:
        purpose = EmailCodePurposeEnum.REGISTRATION
    else:
        purpose = EmailCodePurposeEnum.LOGIN

    try:
        await mediator.send(
            ResendCodeCommand(email=confirmation.email, purpose=purpose)
        )
    except ResendCooldownError as exc:
        return error(
            StatusCodeEnum.TOO_MANY_REQUESTS,
            AuthExceptionMessageEnum.RESEND_COOLDOWN,
            RetryAfterSchema(retry_after=exc.retry_after),
        )
    except ResendNotAllowedError:
        return error(
            StatusCodeEnum.FORBIDDEN,
            AuthExceptionMessageEnum.RESEND_NOT_ALLOWED,
        )

    return ok(RetryAfterSchema(retry_after=code_settings.resend_cooldown_seconds))


@api_router.post(
    AuthPathEnum.API_LOGOUT,
    summary=AuthSummaryEnum.API_LOGOUT,
    tags=["Auth API"],
    responses={
        StatusCodeEnum.OK: {
            "model": BaseResponse,
            "description": AuthSuccessMessageEnum.LOGOUT,
        },
        **INTERNAL_RESPONSE,
    },
)
async def logout_user(
    cookies: FromDishka[CookieSettings],
) -> JSONResponse:
    response = ok()
    clear_auth_cookie(response, ACCESS_COOKIE, cookies)
    clear_auth_cookie(response, PENDING_COOKIE, cookies)
    return response
