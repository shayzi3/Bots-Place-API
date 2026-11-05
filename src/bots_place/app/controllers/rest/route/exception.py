import logging
from collections.abc import Callable, Coroutine
from typing import Any

from dishka.integrations.fastapi import DishkaRoute
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from starlette.exceptions import HTTPException as StarletteHTTPException

from bots_place.app.controllers.rest.response import BaseResponse
from bots_place.app.controllers.rest.templates import templates
from bots_place.app.core.api_path import AuthPathEnum
from bots_place.app.core.doc.base_exception_msg import BaseExceptionMessageEnum
from bots_place.app.core.doc.status_code import StatusCodeEnum

logger = logging.getLogger(__name__)


class BaseExceptionRoute(DishkaRoute):
    def get_route_handler(
        self,
    ) -> Callable[[Request], Coroutine[Any, Any, Response]]:
        handler = super().get_route_handler()

        async def wrapped(request: Request) -> Response:
            try:
                return await handler(request)
            except RequestValidationError as ex:
                return self._request_validation_response(ex)
            except StarletteHTTPException:
                raise
            except Exception:
                logger.exception(
                    "Unhandled error on %s %s", request.method, request.url.path
                )
                return self.error_response(request)

        return wrapped

    def _request_validation_response(self, ex: RequestValidationError) -> Response:
        errors = ex.errors()
        detail = str(errors[0]["msg"]) if errors else ""
        body: Any = BaseResponse(
            status_code=StatusCodeEnum.UNPROCESSABLE_ENTITY,
            msg=BaseExceptionMessageEnum.VALIDATION_ERROR.format(detail),
        )
        return JSONResponse(
            status_code=StatusCodeEnum.UNPROCESSABLE_ENTITY,
            content=body.model_dump(),
        )

    def error_response(self, request: Request) -> Response:
        raise NotImplementedError


class ApiExceptionRoute(BaseExceptionRoute):
    def error_response(self, request: Request) -> Response:
        body: Any = BaseResponse(
            status_code=StatusCodeEnum.INTERNAL_SERVER_ERROR,
            msg=BaseExceptionMessageEnum.INTERNAL_ERROR,
        )
        return JSONResponse(
            status_code=StatusCodeEnum.INTERNAL_SERVER_ERROR,
            content=body.model_dump(),
        )


class TemplateExceptionRoute(BaseExceptionRoute):
    def error_response(self, request: Request) -> Response:
        return templates.TemplateResponse(
            request,
            "error.html",
            {
                "login_url": AuthPathEnum.PAGE_LOGIN,
                "google_url": "#",
                "message": BaseExceptionMessageEnum.INTERNAL_ERROR,
            },
            status_code=StatusCodeEnum.INTERNAL_SERVER_ERROR,
        )
