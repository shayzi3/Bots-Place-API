from enum import StrEnum


class AuthSummaryEnum(StrEnum):
    PAGE_LOGIN = "Login page"
    PAGE_REGISTER = "Register page"
    PAGE_CONFIRM = "Confirm page"
    API_LOGIN = "Login user"
    API_REGISTER = "Register user"
    API_CONFIRM = "Confirm email code"
    API_RESEND = "Resend email code"
    API_LOGOUT = "Logout user"
    GOOGLE_LOGIN = "Login with Google"
    GOOGLE_CALLBACK = "Google sign-in callback"
