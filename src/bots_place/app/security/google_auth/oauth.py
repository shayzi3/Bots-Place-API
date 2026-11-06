import httpx
from authlib.integrations.base_client import OAuthError
from authlib.integrations.starlette_client import OAuth
from starlette.requests import Request
from starlette.responses import Response

from bots_place.app.security.google_auth.base import GoogleAuth, GoogleUserInfo
from bots_place.config.env import GoogleSettings
from bots_place.domain.exceptions.google import (
    GoogleAuthFailedError,
    GoogleEmailNotVerifiedError,
)

GOOGLE_METADATA_URL = "https://accounts.google.com/.well-known/openid-configuration"


class AuthlibGoogleAuth(GoogleAuth):
    def __init__(self, settings: GoogleSettings) -> None:
        self._settings = settings
        oauth = OAuth()
        self._client = oauth.register(
            name="google",
            client_id=settings.client_id,
            client_secret=settings.client_secret,
            server_metadata_url=GOOGLE_METADATA_URL,
            client_kwargs={
                "scope": "openid email profile",
                "code_challenge_method": "S256",
            },
        )

    async def authorize_redirect(self, request: Request) -> Response:
        try:
            return await self._client.authorize_redirect(
                request, self._settings.redirect_uri
            )
        except (OAuthError, httpx.HTTPError) as exc:
            raise GoogleAuthFailedError from exc

    async def fetch_user(self, request: Request) -> GoogleUserInfo:
        try:
            token = await self._client.authorize_access_token(request)
            claims = token["userinfo"]
            email: str = claims["email"]
        except (OAuthError, httpx.HTTPError, KeyError) as exc:
            raise GoogleAuthFailedError from exc

        if not claims.get("email_verified", False):
            raise GoogleEmailNotVerifiedError

        return GoogleUserInfo(
            email=email,
            name=claims.get("name", ""),
            email_verified=True,
        )
