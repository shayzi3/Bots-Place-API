from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from bots_place.app.controllers.rest.route import TemplateExceptionRoute
from bots_place.app.controllers.rest.routers.auth.depends import Confirmation
from bots_place.app.controllers.rest.templates import templates
from bots_place.app.core.api_path import AuthPathEnum
from bots_place.app.core.doc.auth import AuthSummaryEnum

template_router = APIRouter(route_class=TemplateExceptionRoute)


@template_router.get(
    AuthPathEnum.PAGE_LOGIN,
    response_class=HTMLResponse,
    summary=AuthSummaryEnum.PAGE_LOGIN,
    tags=["Auth Template"],
)
async def login_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "login.html",
        {
            "login_url": AuthPathEnum.API_LOGIN,
            "google_url": AuthPathEnum.GOOGLE_LOGIN,
            "register_url": AuthPathEnum.PAGE_REGISTER,
            "error": request.query_params.get("error"),
        },
    )


@template_router.get(
    AuthPathEnum.PAGE_REGISTER,
    response_class=HTMLResponse,
    summary=AuthSummaryEnum.PAGE_REGISTER,
    tags=["Auth Template"],
)
async def register_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "register.html",
        {
            "register_url": AuthPathEnum.API_REGISTER,
            "google_url": AuthPathEnum.GOOGLE_LOGIN,
            "login_url": AuthPathEnum.PAGE_LOGIN,
        },
    )


@template_router.get(
    AuthPathEnum.PAGE_CONFIRM,
    response_class=HTMLResponse,
    summary=AuthSummaryEnum.PAGE_CONFIRM,
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
                "resend_url": AuthPathEnum.API_RESEND,
                "email": confirmation.email,
            },
        )
    return RedirectResponse(AuthPathEnum.PAGE_LOGIN, status_code=303)
