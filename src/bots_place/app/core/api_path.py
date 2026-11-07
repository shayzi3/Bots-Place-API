from enum import StrEnum

VERSION = "v1"
VERSION_PREFIX = f"/api/{VERSION}"


class AuthPathEnum(StrEnum):
    PREFIX = "/auth"
    PAGE_LOGIN = f"{PREFIX}/login"
    PAGE_REGISTER = f"{PREFIX}/register"
    PAGE_CONFIRM = f"{PREFIX}/confirm"
    API_LOGIN = f"{VERSION_PREFIX}{PREFIX}/login"
    API_REGISTER = f"{VERSION_PREFIX}{PREFIX}/register"
    API_CONFIRM = f"{VERSION_PREFIX}{PREFIX}/confirm"
    API_RESEND = f"{VERSION_PREFIX}{PREFIX}/resend"
    API_LOGOUT = f"{VERSION_PREFIX}{PREFIX}/logout"
    GOOGLE_LOGIN = f"{PREFIX}/google"
    GOOGLE_CALLBACK = f"{PREFIX}/google/callback"


class RootPathEnum(StrEnum):
    PAGE_ROOT = "/"


class UserPathEnum(StrEnum):
    PREFIX = "/user"
    API_USER = f"{VERSION_PREFIX}{PREFIX}"
