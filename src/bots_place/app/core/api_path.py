from enum import StrEnum

VERSION = "v1"
VERSION_PREFIX = f"/api/{VERSION}"


class ApiPathEnum(StrEnum):
    PREFIX = "/auth"
    PAGE = f"{VERSION_PREFIX}{PREFIX}"
    LOGIN = f"{VERSION_PREFIX}{PREFIX}/login"
    REGISTER = f"{VERSION_PREFIX}{PREFIX}/register"
    LOGOUT = f"{VERSION_PREFIX}{PREFIX}/logout"
