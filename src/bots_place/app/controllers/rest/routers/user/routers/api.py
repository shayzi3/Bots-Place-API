from fastapi import APIRouter
from fastapi.responses import JSONResponse

from bots_place.app.controllers.rest.depends import CurrentUser
from bots_place.app.controllers.rest.response import (
    INTERNAL_RESPONSE,
    UNAUTHORIZED_RESPONSE,
    BaseResponse,
    error,
    ok,
)
from bots_place.app.controllers.rest.route import ApiExceptionRoute
from bots_place.app.controllers.rest.routers.user.schema import UserProfileSchema
from bots_place.app.core.api_path import UserPathEnum
from bots_place.app.core.doc.base_exception_msg import BaseExceptionMessageEnum
from bots_place.app.core.doc.status_code import StatusCodeEnum
from bots_place.app.core.doc.user.success_msg import UserSuccessMessageEnum

user_api_router = APIRouter(route_class=ApiExceptionRoute)


@user_api_router.get(
    UserPathEnum.API_USER,
    tags=["User API"],
    responses={
        StatusCodeEnum.OK: {
            "model": BaseResponse[UserProfileSchema],
            "description": UserSuccessMessageEnum.PROFILE,
        },
        **UNAUTHORIZED_RESPONSE,
        **INTERNAL_RESPONSE,
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
