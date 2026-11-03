from fastapi.security.oauth2 import OAuth2PasswordBearer

from bots_place.app.core.api_path import ApiPathEnum

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=ApiPathEnum.LOGIN)
