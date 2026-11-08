from typing import Any

from fastapi.responses import JSONResponse
from pydantic import BaseModel

from bots_place.app.core.doc.base_exception_msg import BaseExceptionMessageEnum
from bots_place.app.core.doc.status_code import StatusCodeEnum


class BaseResponse[Data: BaseModel](BaseModel):
    status_code: int
    msg: str | None = None
    data: Data | None = None


def error_responses(
    *,
    internal: bool = False,
    unauthorized: bool = False,
    validation: bool = False,
) -> dict[int | str, dict[str, Any]]:
    responses: dict[int | str, dict[str, Any]] = {}
    if internal:
        responses[StatusCodeEnum.INTERNAL_SERVER_ERROR] = {
            "model": BaseResponse,
            "description": BaseExceptionMessageEnum.INTERNAL_ERROR,
        }
    if unauthorized:
        responses[StatusCodeEnum.UNAUTHORIZED] = {
            "model": BaseResponse,
            "description": BaseExceptionMessageEnum.NOT_AUTHENTICATED,
        }
    if validation:
        responses[StatusCodeEnum.UNPROCESSABLE_ENTITY] = {
            "model": BaseResponse,
            "description": BaseExceptionMessageEnum.VALIDATION_ERROR,
        }
    return responses


def ok(data: BaseModel | None = None, msg: str | None = None) -> JSONResponse:
    body: Any = BaseResponse(status_code=StatusCodeEnum.OK, msg=msg, data=data)
    return JSONResponse(
        status_code=StatusCodeEnum.OK,
        content=body.model_dump(serialize_as_any=True, mode="json"),
    )


def error(
    status_code: StatusCodeEnum,
    message: str,
    data: BaseModel | None = None,
) -> JSONResponse:
    body: Any = BaseResponse(
        status_code=status_code,
        msg=message,
        data=data,
    )
    return JSONResponse(
        status_code=status_code, content=body.model_dump(serialize_as_any=True)
    )
