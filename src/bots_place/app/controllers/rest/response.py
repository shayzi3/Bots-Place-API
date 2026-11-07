from typing import Any

from fastapi.responses import JSONResponse
from pydantic import BaseModel

from bots_place.app.core.doc.base_exception_msg import BaseExceptionMessageEnum
from bots_place.app.core.doc.status_code import StatusCodeEnum


class BaseResponse[Data: BaseModel](BaseModel):
    status_code: int
    msg: str | None = None
    data: Data | None = None


INTERNAL_RESPONSE: dict[int | str, dict[str, Any]] = {
    StatusCodeEnum.INTERNAL_SERVER_ERROR: {
        "model": BaseResponse,
        "description": BaseExceptionMessageEnum.INTERNAL_ERROR,
    },
}

UNAUTHORIZED_RESPONSE: dict[int | str, dict[str, Any]] = {
    StatusCodeEnum.UNAUTHORIZED: {
        "model": BaseResponse,
        "description": BaseExceptionMessageEnum.NOT_AUTHENTICATED,
    },
}


def ok(data: BaseModel | None = None) -> JSONResponse:
    body: Any = BaseResponse(status_code=StatusCodeEnum.OK, data=data)
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
