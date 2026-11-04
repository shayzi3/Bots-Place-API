from typing import Annotated

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from bots_place.app.controllers.rest.routers.auth.utils.cookies import (
    ACCESS_COOKIE,
    PENDING_COOKIE,
    clear_auth_cookie,
    set_auth_cookie,
)
from bots_place.app.controllers.rest.templates import templates
from bots_place.app.core.api_path import AuthPathEnum
from bots_place.app.security.tokens import (
    ConfirmationPurpose,
    TokenService,
)
from bots_place.config.env import CookieSettings
from bots_place.domain.commands import (
    ConfirmLoginCommand,
    ConfirmRegistrationCommand,
    RegisterUserCommand,
    RequestLoginCodeCommand,
)
from bots_place.domain.exceptions.user import (
    EmailAlreadyExistsError,
    InvalidEmailCodeError,
    LoginNotAllowedError,
)
from bots_place.infrastructure.mediator import Mediator

from .depends import Confirmation
from .doc import AuthApiDescriptionEnum, AuthPageDescriptionEnum
from .schema.confirm import ConfirmCodeForm

auth_router = APIRouter(route_class=DishkaRoute)


@auth_router.get(
    AuthPathEnum.PAGE_LOGIN,
    response_class=HTMLResponse,
    summary=AuthPageDescriptionEnum.LOGIN,
    tags=["Auth Template"],
)
async def login_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "login.html",
        {
            "login_url": AuthPathEnum.API_LOGIN,
            "google_url": "#",
            "register_url": AuthPathEnum.PAGE_REGISTER,
            "error": request.query_params.get("error"),
        },
    )


@auth_router.get(
    AuthPathEnum.PAGE_REGISTER,
    response_class=HTMLResponse,
    summary=AuthPageDescriptionEnum.REGISTER,
    tags=["Auth Template"],
)
async def register_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "register.html",
        {
            "register_url": AuthPathEnum.API_REGISTER,
            "google_url": "#",
            "login_url": AuthPathEnum.PAGE_LOGIN,
        },
    )


@auth_router.post(
    AuthPathEnum.API_REGISTER,
    summary=AuthApiDescriptionEnum.REGISTER,
    tags=["Auth API"],
)
async def register_user(
    command: Annotated[RegisterUserCommand, Form()],
    mediator: FromDishka[Mediator],
    tokens: FromDishka[TokenService],
    cookies: FromDishka[CookieSettings],
) -> RedirectResponse:
    try:
        await mediator.send(command)
    except EmailAlreadyExistsError:
        return RedirectResponse(AuthPathEnum.PAGE_LOGIN, status_code=303)

    confirmation = tokens.create_confirmation(
        command.email, ConfirmationPurpose.REGISTER
    )
    response = RedirectResponse(AuthPathEnum.PAGE_CONFIRM, status_code=303)
    set_auth_cookie(
        response,
        PENDING_COOKIE,
        confirmation,
        tokens.confirmation_ttl_seconds,
        cookies,
    )
    return response


@auth_router.post(
    AuthPathEnum.API_LOGIN, summary=AuthApiDescriptionEnum.LOGIN, tags=["Auth API"]
)
async def login_user(
    command: Annotated[RequestLoginCodeCommand, Form()],
    mediator: FromDishka[Mediator],
    tokens: FromDishka[TokenService],
    cookies: FromDishka[CookieSettings],
) -> RedirectResponse:
    try:
        await mediator.send(command)
    except LoginNotAllowedError:
        return RedirectResponse(
            f"{AuthPathEnum.PAGE_LOGIN}?error=login", status_code=303
        )

    confirmation = tokens.create_confirmation(command.email, ConfirmationPurpose.LOGIN)
    response = RedirectResponse(AuthPathEnum.PAGE_CONFIRM, status_code=303)
    set_auth_cookie(
        response,
        PENDING_COOKIE,
        confirmation,
        tokens.confirmation_ttl_seconds,
        cookies,
    )
    return response


@auth_router.get(
    AuthPathEnum.PAGE_CONFIRM,
    response_class=HTMLResponse,
    summary=AuthPageDescriptionEnum.CONFIRM,
    response_model=None,
    tags=["Auth Template"],
)
async def confirm_page(
    request: Request,
    confirmation: Confirmation,
) -> HTMLResponse | RedirectResponse:
    if confirmation is not None:
        return templates.TemplateResponse(
            request,
            "confirm.html",
            {
                "confirm_url": AuthPathEnum.API_CONFIRM,
                "google_url": "#",
                "email": confirmation.email,
                "error": request.query_params.get("error"),
            },
        )
    return RedirectResponse(AuthPathEnum.PAGE_LOGIN, status_code=303)


@auth_router.post(
    AuthPathEnum.API_CONFIRM, summary=AuthApiDescriptionEnum.CONFIRM, tags=["Auth API"]
)
async def confirm(
    confirmation: Confirmation,
    form: Annotated[ConfirmCodeForm, Form()],
    mediator: FromDishka[Mediator],
    tokens: FromDishka[TokenService],
    cookies: FromDishka[CookieSettings],
) -> RedirectResponse:
    if confirmation is None:
        return RedirectResponse(AuthPathEnum.PAGE_LOGIN, status_code=303)

    command: ConfirmRegistrationCommand | ConfirmLoginCommand
    if confirmation.purpose is ConfirmationPurpose.REGISTER:
        command = ConfirmRegistrationCommand(email=confirmation.email, code=form.code)
    elif confirmation.purpose is ConfirmationPurpose.LOGIN:
        command = ConfirmLoginCommand(email=confirmation.email, code=form.code)
    else:
        return RedirectResponse(AuthPathEnum.PAGE_LOGIN, status_code=303)

    try:
        user = await mediator.send(command)
    except InvalidEmailCodeError:
        return RedirectResponse(
            f"{AuthPathEnum.PAGE_CONFIRM}?error=code", status_code=303
        )

    access = tokens.create_access(user.id, user.email)
    response = RedirectResponse("/", status_code=303)
    clear_auth_cookie(response, PENDING_COOKIE, cookies)
    set_auth_cookie(response, ACCESS_COOKIE, access, tokens.access_ttl_seconds, cookies)
    return response


@auth_router.post(
    AuthPathEnum.API_LOGOUT, summary=AuthApiDescriptionEnum.LOGOUT, tags=["Auth API"]
)
async def logout_user(
    cookies: FromDishka[CookieSettings],
) -> RedirectResponse:
    response = RedirectResponse(AuthPathEnum.PAGE_LOGIN, status_code=303)
    clear_auth_cookie(response, ACCESS_COOKIE, cookies)
    clear_auth_cookie(response, PENDING_COOKIE, cookies)
    return response
