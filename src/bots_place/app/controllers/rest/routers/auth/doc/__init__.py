from enum import StrEnum


class AuthDesctriptionEnum(StrEnum):
    LOGIN = "Login to the system"
    REGISTER = "Register a new user"
    LOGOUT = "Logout from the system"


class AuthFormDescriptionEnum(StrEnum):
    EMAIL = "Email address"
