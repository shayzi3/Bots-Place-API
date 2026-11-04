from enum import StrEnum


class AuthPageDescriptionEnum(StrEnum):
    LOGIN = "Login page"
    REGISTER = "Register page"
    CONFIRM = "Confirm page"


class AuthApiDescriptionEnum(StrEnum):
    LOGIN = "Login user"
    REGISTER = "Register user"
    CONFIRM = "Confirm email code"
    LOGOUT = "Logout user"
