from typing import Annotated, Any

from dishka.integrations.fastapi import FromDishka
from fastapi import APIRouter, Form, Request
from fastapi.responses import JSONResponse, RedirectResponse, Response

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
    clear_auth_cookie,
    clear_request_session,
    set_auth_cookie,
    set_request_session_confirmation,
)
from bots_place.app.core.api_path import AuthPathEnum
from bots_place.app.core.doc.auth import AuthSummaryEnum
from bots_place.app.core.doc.auth.exception_msg import AuthExceptionMessageEnum
from bots_place.app.core.doc.auth.success_msg import AuthSuccessMessageEnum
from bots_place.app.core.doc.base_exception_msg import BaseExceptionMessageEnum
from bots_place.app.core.doc.status_code import StatusCodeEnum
from bots_place.app.security.google_auth.base import GoogleAuth
from bots_place.app.security.tokens import (
    ConfirmationPurpose,
    TokenService,
)
from bots_place.config.env import CodeSettings, CookieSettings
from bots_place.domain.commands import (
    ConfirmLoginCommand,
    ConfirmRegistrationCommand,
    GoogleLoginCommand,
    RegisterUserCommand,
    RequestLoginCodeCommand,
    ResendCodeCommand,
)
from bots_place.domain.entities.email_code import EmailCodePurposeEnum
from bots_place.domain.exceptions.google import GoogleAuthError
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
            "model": BaseResponse[RetryAfterSchema],
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
    code_settings: FromDishka[CodeSettings],
    request: Request,
) -> JSONResponse:
    try:
        await mediator.send(command)
    except EmailAlreadyExistsError:
        return error(
            StatusCodeEnum.CONFLICT,
            AuthExceptionMessageEnum.EMAIL_ALREADY_EXISTS,
        )

    set_request_session_confirmation(
        request=request,
        email=command.email,
        purpose=ConfirmationPurpose.REGISTER,
        ttl_seconds=tokens.confirmation_ttl_seconds,
    )
    return ok(RetryAfterSchema(retry_after=code_settings.resend_cooldown_seconds))


@api_router.post(
    AuthPathEnum.API_LOGIN,
    summary=AuthSummaryEnum.API_LOGIN,
    tags=["Auth API"],
    responses={
        StatusCodeEnum.OK: {
            "model": BaseResponse[RetryAfterSchema],
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
    code_settings: FromDishka[CodeSettings],
    request: Request,
) -> JSONResponse:
    try:
        await mediator.send(command)
    except LoginNotAllowedError:
        return error(
            StatusCodeEnum.FORBIDDEN,
            AuthExceptionMessageEnum.LOGIN_NOT_ALLOWED,
        )

    set_request_session_confirmation(
        request=request,
        email=command.email,
        purpose=ConfirmationPurpose.LOGIN,
        ttl_seconds=tokens.confirmation_ttl_seconds,
    )
    return ok(RetryAfterSchema(retry_after=code_settings.resend_cooldown_seconds))


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
    request: Request,
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
    clear_request_session(request)
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
    tokens: FromDishka[TokenService],
    request: Request,
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

    set_request_session_confirmation(
        request=request,
        email=confirmation.email,
        purpose=confirmation.purpose,
        ttl_seconds=tokens.confirmation_ttl_seconds,
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
    cookies: FromDishka[CookieSettings], request: Request
) -> JSONResponse:
    response = ok()
    clear_auth_cookie(response, ACCESS_COOKIE, cookies)
    clear_request_session(request)
    return response


@api_router.get(
    AuthPathEnum.GOOGLE_LOGIN,
    summary=AuthSummaryEnum.GOOGLE_LOGIN,
    tags=["Auth API"],
)
async def google_login(
    request: Request,
    google: FromDishka[GoogleAuth],
) -> Response:
    return await google.authorize_redirect(request)


@api_router.get(
    AuthPathEnum.GOOGLE_CALLBACK,
    summary=AuthSummaryEnum.GOOGLE_CALLBACK,
    tags=["Auth API"],
)
async def google_callback(
    request: Request,
    google: FromDishka[GoogleAuth],
    mediator: FromDishka[Mediator],
    tokens: FromDishka[TokenService],
    cookies: FromDishka[CookieSettings],
) -> RedirectResponse:
    try:
        info = await google.fetch_user(request)
        user = await mediator.send(
            GoogleLoginCommand(email=info.email, username=info.name)
        )
    except GoogleAuthError:
        return RedirectResponse(
            f"{AuthPathEnum.PAGE_LOGIN}?error=google",
            status_code=StatusCodeEnum.SEE_OTHER,
        )

    access = tokens.create_access(user.id, user.email)
    response = RedirectResponse("/", status_code=StatusCodeEnum.SEE_OTHER)
    set_auth_cookie(response, ACCESS_COOKIE, access, tokens.access_ttl_seconds, cookies)
    return response
