from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse

from bots_place.app.core.api_path import ApiPathEnum

from .form.auth_form import EmailAuthForm
from .schema.token import TokenSchema

auth_router = APIRouter(prefix=ApiPathEnum.PREFIX, tags=["Auth"])


@auth_router.get(ApiPathEnum.PAGE, response_class=HTMLResponse, summary="Login page")
async def login_page():
    return "<h1>Login Page</h1>"


@auth_router.post(ApiPathEnum.REGISTER, summary="Register user")
async def register_user():
    pass


@auth_router.post(
    ApiPathEnum.LOGIN,
    summary="Login user",
    response_model=TokenSchema,
    responses={200: {"description": "Successful login", "model": TokenSchema}},
)
async def login_user(
    email_form: Annotated[EmailAuthForm, Depends()],
) -> TokenSchema:
    raise NotImplementedError


@auth_router.post(ApiPathEnum.LOGOUT, summary="Logout user")
async def logout_user():
    pass
