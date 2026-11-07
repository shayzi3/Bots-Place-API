from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from bots_place.app.controllers.rest.depends import CurrentUser
from bots_place.app.controllers.rest.route import TemplateExceptionRoute
from bots_place.app.controllers.rest.templates import templates
from bots_place.app.core.api_path import AuthPathEnum, RootPathEnum, UserPathEnum

root_template_router = APIRouter(route_class=TemplateExceptionRoute)


@root_template_router.get(
    RootPathEnum.PAGE_ROOT,
    response_class=HTMLResponse,
    tags=["Root"],
)
async def root_page(request: Request, user: CurrentUser) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "root.html",
        {
            "is_authenticated": user is not None,
            "login_url": AuthPathEnum.PAGE_LOGIN,
            "profile_url": UserPathEnum.API_USER,
        },
    )
