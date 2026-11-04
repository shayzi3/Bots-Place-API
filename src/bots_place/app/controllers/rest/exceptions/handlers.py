import logging

from fastapi import FastAPI, Request
from fastapi.responses import Response

from bots_place.app.controllers.rest.templates import templates
from bots_place.app.core.api_path import AuthPathEnum

logger = logging.getLogger(__name__)


async def unhandled_exception_handler(request: Request, exc: Exception) -> Response:
    logger.error(
        "Unhandled error on %s %s",
        request.method,
        request.url.path,
        exc_info=exc,
    )
    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "login_url": AuthPathEnum.PAGE_LOGIN,
            "google_url": "#",
        },
        status_code=500,
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(Exception, unhandled_exception_handler)
